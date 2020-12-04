import os
import re
import time
from datetime import date
from typing import Any, Dict, Optional, Sequence, Tuple
from urllib.parse import quote

import requests
import unidecode
import xmltodict
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import TrigramSimilarity
from django.db import models
from django.db.models import F, Q, Sum, signals
from django.db.models.functions import Lower
from django.db.models.indexes import Index
from django.urls import reverse
from django.utils import timezone

from library.signals import update_timestamp_on_save
from library.utils import LANGUAGES, isbn_to_isbn10, oxford_comma, str2bool

from .author import Author

LogEntry = models.Model


class BookManager(models.Manager):  # type: ignore [type-arg]
    def get_queryset(self) -> "BookQuerySet":
        return BookQuerySet(self.model, using=self._db)

    def by_gender(self, *genders: int) -> "BookQuerySet":
        return self.get_queryset().by_gender(*genders)

    def by_men(self) -> "BookQuerySet":
        return self.get_queryset().by_men()

    def by_women(self) -> "BookQuerySet":
        return self.get_queryset().by_women()

    def by_multiple_genders(self) -> "BookQuerySet":
        return self.get_queryset().by_multiple_genders()

    def fiction(self) -> "BookQuerySet":
        return self.get_queryset().fiction()

    def nonfiction(self) -> "BookQuerySet":
        return self.get_queryset().nonfiction()

    def read(self) -> "BookQuerySet":
        return self.get_queryset().read()

    def unread(self) -> "BookQuerySet":
        return self.get_queryset().unread()

    def search(self, pattern: str) -> "BookQuerySet":
        return (
            self.annotate(  # type: ignore [return-value]
                title_similarity=TrigramSimilarity("title", pattern),
                subtitle_similarity=TrigramSimilarity("subtitle", pattern),
                series_similarity=TrigramSimilarity("series", pattern),
                edition_title_similarity=TrigramSimilarity("edition_title", pattern),
                edition_subtitle_similarity=TrigramSimilarity(
                    "edition_subtitle", pattern
                ),
                similarity=(
                    F("title_similarity")
                    + F("subtitle_similarity")
                    + F("series_similarity")
                    + F("edition_title_similarity")
                    + F("edition_subtitle_similarity")
                ),
            )
            .order_by("-similarity")
            .filter(similarity__gt=0.14)
        )

    def filter_by_request(self, request: str) -> "BookQuerySet":
        return self.get_queryset().filter_by_request(request)

    def filter_by_format(self, edition_format: str) -> "BookQuerySet":
        return self.get_queryset().filter_by_format(edition_format)

    def find_on_goodreads(self, query: str) -> Optional[Sequence[Dict[str, Any]]]:
        search_url = f"https://www.goodreads.com/search/index.xml?key={os.environ['GOODREADS_KEY']}&q={query}"
        data = requests.get(search_url).text
        xml = xmltodict.parse(data, dict_constructor=dict)

        try:
            all_results = xml["GoodreadsResponse"]["search"]["results"]["work"]
        except KeyError:
            return None
        except TypeError:
            return None

        results: Sequence[Dict[str, Any]] = []
        if "id" in all_results:
            results = [all_results]
        else:
            results = all_results

        return results

    def create_from_goodreads(
        self, query: Optional[str] = None, data: Optional[Dict[str, Any]] = None
    ) -> Optional["Book"]:
        result = {}
        if query and not data:
            results = self.find_on_goodreads(query)
            if not results:
                return None
            result = results[0]
        elif data:
            result = data
        else:
            return None

        goodreads_book = result["best_book"]

        title = goodreads_book["title"].strip()
        series_name = ""
        series_order = None

        if title.endswith(")"):
            title, rest = title.split(" (", 2)
            first_series = rest.split(";")[0]
            series_name, *rest = first_series.split("#")
            series_name = series_name.strip(" ,)")
            if rest:
                try:
                    series_order = float(rest[0].strip(")"))
                except ValueError:
                    pass

        book = Book(
            title=title,
            series=series_name,
            series_order=series_order,
            goodreads_id=goodreads_book["id"]["#text"],
            first_published=result["original_publication_year"].get("#text"),
        )

        if "nophoto" not in goodreads_book["image_url"]:
            book.image_url = goodreads_book["image_url"]

        if not book.image_url:
            book.image_url = Book.objects.scrape_goodreads_image(book.goodreads_id)

        book.first_author, created = Author.objects.get_or_create_by_single_name(
            goodreads_book["author"]["name"]
        )

        if query:
            if len(query) == 13 and query.startswith("978"):
                book.isbn = query
            elif re.match(r"^B[A-Z0-9]{9}$", query):
                book.asin = query
                book.edition_format = Book.Format.EBOOK

        book.save()

        if book.isbn or book.google_books_id:
            if (
                (book.isbn and not book.google_books_id)
                or not book.publisher
                or not book.page_count
                or not book.first_published
            ):
                book.update_from_google()
                book.refresh_from_db()

        return book

    def regenerate_all_slugs(self) -> None:
        qs = self.get_queryset()
        qs.update(slug="")
        for book in qs:
            book.slug = book._generate_slug()
            book.save()

    def update_all_from_google(self) -> None:
        candidate_ids = list(
            self.get_queryset()
            .exclude(isbn="", google_books_id="")
            .filter(
                Q(publisher="")
                | Q(page_count__isnull=True)
                | Q(page_count=0)
                | Q(google_books_id="")
                | Q(first_published=0)
                | Q(first_published__isnull=True)
            )
            .values_list("id", flat=True)
        )
        print(f"updating {len(candidate_ids)} books")

        sleep_time = 1
        while candidate_ids:
            candidate_id = candidate_ids.pop(0)
            candidate = Book.objects.get(pk=candidate_id)
            if candidate.update_from_google():
                sleep_time = 1
                print(".", end="", flush=True)
                if (count := len(candidate_ids)) % 20 == 0:
                    print(f"{count} remaining")
            else:
                candidate_ids.append(candidate_id)
                print(f"sleeping {sleep_time}")
                time.sleep(sleep_time)
                sleep_time *= 2

    def scrape_goodreads_image(self, goodreads_id: str) -> str:
        goodreads_url = f"https://www.goodreads.com/book/show/{goodreads_id}"
        text = requests.get(goodreads_url).text
        meta_tag = re.search(r"<meta[^>]*og:image[^>]*>", text)
        if meta_tag:
            image_url = re.search(r"https://.*\.jpg", meta_tag[0])
            if image_url and ("nophoto" not in image_url[0]):
                return image_url[0]

        return ""


class BookQuerySet(models.QuerySet):  # type: ignore [type-arg]
    def by_gender(self, *genders: int) -> "BookQuerySet":
        return self.filter(
            Q(first_author__gender__in=genders)
            | Q(additional_authors__gender__in=genders)
        ).distinct()

    def by_men(self) -> "BookQuerySet":
        return self.by_gender(1)

    def by_women(self) -> "BookQuerySet":
        return self.by_gender(2)

    def by_multiple_genders(self) -> "BookQuerySet":
        return (
            self.exclude(additional_authors__isnull=True)
            .filter(additional_authors__gender__ne=F("first_author__gender"))
            .distinct()
        )

    def tagged(self, *tag_names: str) -> "BookQuerySet":
        qs = self.distinct()
        for tag_name in tag_names:
            qs &= Tag.objects[tag_name].books
        return qs

    def fiction(self) -> "BookQuerySet":
        return self.tagged("fiction")

    def nonfiction(self) -> "BookQuerySet":
        return self.tagged("non-fiction")

    def read(self) -> "BookQuerySet":
        return self.filter(
            Q(log_entries__end_date__isnull=False)
            | Q(parent_edition__log_entries__end_date__isnull=False)
        ).distinct()

    def unread(self) -> "BookQuerySet":
        return self.filter(
            Q(log_entries__end_date__isnull=True)
            & Q(parent_edition__log_entries__end_date__isnull=True)
        ).distinct()

    def poc(self, is_poc: bool = True) -> "BookQuerySet":
        return self.filter(
            Q(first_author__poc=is_poc) | Q(additional_authors__poc=is_poc)
        )

    def filter_by_request(self, request: Any) -> "BookQuerySet":
        qs = self
        if gender := request.GET.get("gender"):
            if gender.lower() == "multiple":
                qs = qs.by_multiple_genders()
            elif gender.lower() == "nonmale":
                qs = qs.by_gender(0, 2, 4)
            else:
                if not gender.isdigit():
                    gender = Author.Gender[gender.upper()]
                qs = qs.by_gender(gender)
        if poc := request.GET.get("poc"):
            qs = qs.poc(str2bool(poc))
        if tags := request.GET.get("tags"):
            qs = qs.tagged(*[tag.strip() for tag in tags.lower().split(",")])
        if owned := request.GET.get("owned"):
            try:
                val = not str2bool(owned)
                qs = qs.filter(owned_by__isnull=val)
            except ValueError:
                qs = qs.filter(owned_by__username=owned)
        if want_to_read := request.GET.get("want_to_read"):
            qs = qs.filter(want_to_read=str2bool(want_to_read))
        if read := request.GET.get("read"):
            if str2bool(read):
                qs = qs.read()
            else:
                qs = qs.unread()

        return qs

    def filter_by_format(self, edition_format: str) -> "BookQuerySet":
        edition_format = edition_format.strip("s").upper()
        if edition_format == "PHYSICAL":
            books = self.filter(
                Q(edition_format=Book.Format["PAPERBACK"])
                | Q(edition_format=Book.Format["HARDBACK"])
            )
        elif edition_format == "EBOOK":
            books = self.filter(
                Q(edition_format=Book.Format[edition_format])
                | Q(has_ebook_edition=True)
            )
        else:
            books = self.filter(edition_format=Book.Format[edition_format])

        return books

    @property
    def page_count(self) -> int:
        if count := self.aggregate(Sum("page_count"))["page_count__sum"]:
            return int(count)
        else:
            return 0


class Book(models.Model):
    objects = BookManager()

    class Meta:
        indexes = [
            Index(fields=["series", "series_order", "title"]),
            GinIndex(fields=["tags"]),
        ]
        ordering = [
            Lower("first_author__surname"),
            Lower("first_author__forenames"),
            "series",
            "series_order",
            "title",
        ]

    title = models.CharField(db_index=True, max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    first_author = models.ForeignKey(
        Author, on_delete=models.CASCADE, null=True, related_name="first_authored_books"
    )
    first_author_role = models.CharField(
        db_index=True, max_length=255, blank=True, default=""
    )
    additional_authors = models.ManyToManyField(
        Author,
        through="BookAuthor",
        related_name="additional_authored_books",
        blank=True,
    )

    class Format(models.IntegerChoices):
        UNKNOWN = 0
        PAPERBACK = 1
        HARDBACK = 2
        EBOOK = 3
        WEB = 4

    first_published = models.PositiveSmallIntegerField(blank=True, null=True)
    language = models.CharField(max_length=2, default="en", choices=LANGUAGES)

    series = models.CharField(db_index=True, max_length=255, blank=True)
    series_order = models.FloatField(db_index=True, blank=True, null=True)

    # these at least in theory relate only to an edition, not every edition
    # edition could be a separate models but it would almost always be one-to-one
    edition_published = models.PositiveSmallIntegerField(blank=True, null=True)
    publisher = models.CharField(max_length=255, blank=True)
    edition_format = models.IntegerField(
        db_index=True, choices=Format.choices, default=0
    )
    edition_number = models.PositiveSmallIntegerField(blank=True, null=True)
    page_count = models.PositiveSmallIntegerField(blank=True, null=True)
    goodreads_id = models.CharField(max_length=255, blank=True)
    google_books_id = models.CharField(max_length=255, blank=True)
    isbn = models.CharField(max_length=13, blank=True)
    asin = models.CharField(max_length=255, blank=True)
    edition_language = models.CharField(
        max_length=2, blank=True, choices=LANGUAGES
    )  # i.e., a translation
    edition_title = models.CharField(max_length=255, blank=True)  # if translated
    edition_subtitle = models.CharField(max_length=255, blank=True)  # if translated

    acquired_date = models.DateField(blank=True, null=True)
    alienated_date = models.DateField(blank=True, null=True)
    was_borrowed = models.BooleanField(db_index=True, default=False)
    borrowed_from = models.CharField(max_length=255, blank=True)
    owned_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="owned_books",
    )

    image_url = models.URLField(blank=True)
    publisher_url = models.URLField(blank=True)

    want_to_read = models.BooleanField(db_index=True, default=True)

    tags = ArrayField(models.CharField(max_length=32), default=list, blank=True)

    review = models.TextField(blank=True)
    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        choices=[(i / 2, i / 2) for i in range(1, 11)],
        blank=True,
        null=True,
    )

    has_ebook_edition = models.BooleanField(default=False)
    ebook_isbn = models.CharField(max_length=13, blank=True)
    ebook_asin = models.CharField(max_length=255, blank=True)
    ebook_acquired_date = models.DateField(blank=True, null=True)

    editions = models.ManyToManyField("self", symmetrical=True, blank=True)

    created_date = models.DateTimeField(db_index=True, default=timezone.now)
    modified_date = models.DateTimeField(db_index=True, default=timezone.now)

    slug = models.SlugField(blank=True, default="")

    parent_edition = models.ForeignKey(
        "self",
        related_name="subeditions",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self) -> str:
        if len(self.authors) > 3:
            result = str(self.first_author) + " and others"
        else:
            result = oxford_comma([str(author) for author in self.authors])

        result += ", " + self.display_title

        if (
            self.editions.count()
            and self.edition_format
            and self.edition_title
            in self.editions.all().values_list("edition_title", flat=True)
        ):
            result += f" ({self.get_edition_disambiguator()} edition)"
        return result

    def get_edition_disambiguator(self) -> str:
        if self.editions.exclude(edition_language=self.edition_language).count():
            if self.edition_language:
                return self.get_edition_language_display()
            else:
                return self.get_language_display()
        else:
            return self.get_edition_format_display().lower()

    def get_absolute_url(self) -> str:
        return reverse("library:book_details", args=[self.slug])

    @property
    def authors(self) -> Sequence[Author]:
        additional_authors = list(
            self.additional_authors.filter(
                bookauthor__role=self.first_author_role
            ).order_by("bookauthor__order")
        )
        if self.first_author:
            return [self.first_author] + additional_authors
        else:
            return additional_authors

    @property
    def all_authors(self) -> Sequence[Author]:
        additional_authors = list(self.additional_authors.order_by("bookauthor__order"))
        if self.first_author:
            return [self.first_author] + additional_authors
        else:
            return additional_authors

    @property
    def all_authors_editors(self) -> bool:
        return len(self.authors) > 1 and all(
            (author.is_editor_of(self) for author in self.all_authors)
        )

    @property
    def has_full_authors(self) -> bool:
        return len(self.authors) > 3 or self.authors != self.all_authors

    @property
    def display_title(self) -> str:
        if self.edition_title:
            return self.edition_title + (
                ": " + self.edition_subtitle if self.edition_subtitle else ""
            )
        else:
            return self.title + (": " + self.subtitle if self.subtitle else "")

    @property
    def display_date(self) -> str:
        if (
            self.edition_published
            and self.first_published
            and self.edition_published != self.first_published
        ):
            return f"[{self.first_published}] {self.edition_published}"
        elif self.edition_published:
            return str(self.edition_published)
        elif self.first_published:
            return str(self.first_published)
        else:
            return "n.d."

    def add_author(
        self, author: "Author", role: str = "", order: Optional[int] = None
    ) -> None:
        if author.id is not self.first_author_id and author not in self.authors:
            if not self.first_author:
                self.first_author = author
                self.first_author_role = role
                self.save()
            else:
                authorship = BookAuthor(
                    book=self, author=author, role=role, order=order
                )
                authorship.save()

    def start_reading(self) -> None:
        if not self.log_entries.filter(end_date=None):
            self.log_entries.create()
            self.want_to_read = False
            self.save()

    def finish_reading(self) -> None:
        entry = self.log_entries.get(end_date=None)
        self.update_progress(percentage=100, page=self.page_count)
        entry.end_date = timezone.now()
        entry.save()

        if self.parent_edition:
            sibling_editions = self.parent_edition.subeditions
            if sibling_editions.count() == sibling_editions.read().count():
                self.parent_edition.finish_reading()

    def update_progress(
        self, percentage: Optional[float] = None, page: Optional[int] = None
    ) -> float:
        if not percentage:
            if not page:
                raise ValueError("Must specify percentage or page")
            elif not self.page_count:
                raise ValueError("Must specify percentage when page count is unset")
            else:
                percentage = page / self.page_count * 100

        entry = self.log_entries.get(end_date=None)
        entry.progress_date = timezone.now()

        entry.progress_page = page or 0
        entry.progress_percentage = percentage
        entry.save()
        return percentage

    def mark_read_sometime(self) -> None:
        self.log_entries.create(start_date=None, end_date="0001-01-01 00:00")

    def mark_owned(self) -> None:
        self.owned_by = User.objects.get(username="ben")
        self.acquired_date = timezone.now()
        self.was_borrowed = False
        self.borrowed_from = ""
        self.save()

    @property
    def currently_reading(self) -> bool:
        entries = self.log_entries.filter(end_date=None).order_by("-start_date")
        if not entries:
            return False
        else:
            return entries[0].currently_reading

    @property
    def display_series(self) -> str:
        if not self.series:
            return ""
        elif self.series_order:
            return f"{self.series}, #{str(self.series_order).replace('.0', '')}"
        else:
            return self.series

    @property
    def read(self) -> bool:
        if self.parent_edition:
            return self.parent_edition.read

        return self.log_entries.filter(end_date__isnull=False).count() > 0

    def create_new_edition(self, edition_format: int) -> None:
        edition = Book(
            title=self.title,
            subtitle=self.subtitle,
            edition_format=edition_format,
            first_author=self.first_author,
            first_author_role=self.first_author_role,
            first_published=self.first_published,
            language=self.language,
            image_url=self.image_url,
            publisher_url=self.publisher_url,
            want_to_read=self.want_to_read,
            series=self.series,
            series_order=self.series_order,
            tags=self.tags,
            review=self.review,
            rating=self.rating,
            # technically this is per-edition but this is convenient
            goodreads_id=self.goodreads_id,
        )
        edition.save()
        for author in self.bookauthor_set.all():
            edition.add_author(author.author, role=author.role, order=author.order)
        self.editions.add(edition)
        self.save()

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = self._generate_slug()

        if "goodreads" in self.image_url or "amazon" in self.image_url:
            self.image_url = re.sub(r"\._.+_\.jpg$", ".jpg", self.image_url)

        if self.first_published == 0:
            self.first_published = None
        if self.edition_published == 0:
            self.edition_published = None
        if self.page_count == 0:
            self.page_count = None
        if self.edition_number == 0:
            self.edition_number = None
        if self.series_order == 0.0:
            self.series_order = None
        if self.rating == 0:
            self.rating = None

        self.tags = sorted(
            set(
                [
                    tag.lower().replace(",", "").replace("/", "").strip()
                    for tag in self.tags
                ]
            )
        )
        for tag in self.tags:
            Tag.objects.get_or_create(name=tag)

        super().save(*args, **kwargs)

        self.editions.all().update(
            title=self.title,
            subtitle=self.subtitle,
            first_author=self.first_author,
            first_author_role=self.first_author_role,
            first_published=self.first_published,
            language=self.language,
            want_to_read=self.want_to_read,
            tags=self.tags,
            review=self.review,
            rating=self.rating,
            series=self.series,
            series_order=self.series_order,
        )

        self.subeditions.all().update(want_to_read=self.want_to_read)

    @property
    def all_log_entries(self) -> "models.QuerySet[LogEntry]":
        entries = self.log_entries.all()
        for edition in self.editions.all():
            entries |= edition.log_entries.all()
        return entries

    def _generate_slug(self) -> str:
        slug = (
            "-".join(self.first_author.slug.split("-")[0:-1]) + "-"
            if self.first_author
            else ""
        )

        stopwords = ["a", "an", "and", "at", "in", "is", "of", "on", "to", "for", "the"]

        title = self.edition_title if self.edition_title else self.title

        title_words = title.split(":")[0].lower().split(" ")
        title_words = [word for word in title_words if word not in stopwords]

        slug += "-".join(title_words)

        slug = unidecode.unidecode(slug)
        slug = re.sub(r"[^\w-]+", "", slug)

        slug = slug[0:50].strip("-")
        matches = Book.objects.filter(slug__regex=f"^{slug}(-\\d+)?$")
        if matches:
            slug = slug[0:48].strip("-") + "-" + str(matches.count())

        return slug

    @property
    def isbn10(self) -> str:
        return isbn_to_isbn10(self.isbn)

    @property
    def owned(self) -> bool:
        return self.owned_by is not None and self.owned_by.username == "ben"

    @property
    def owned_by_sara(self) -> bool:
        return self.owned_by is not None and self.owned_by.username == "sara"

    @property
    def search_query(self) -> str:
        return quote(
            f"{self.edition_title or self.title} {self.first_author and self.first_author.surname}"
        )

    @property
    def ebook_url(self) -> str:
        return f"https://amazon.co.uk/dp/{self.ebook_asin}" if self.ebook_asin else ""

    @property
    def is_translated(self) -> bool:
        return (
            self.edition_language is not None and self.edition_language != self.language
        )

    @property
    def has_original_title(self) -> bool:
        return (not self.edition_title) or self.title == self.edition_title

    @property
    def is_first_edition(self) -> bool:
        return (
            not self.edition_published
        ) or self.edition_published == self.first_published

    def update_from_google(self) -> bool:
        search_url = ""
        if self.google_books_id:
            search_url = (
                f"https://www.googleapis.com/books/v1/volumes/{self.google_books_id}"
            )
        elif self.isbn:
            search_url = (
                f"https://www.googleapis.com/books/v1/volumes?q=isbn:{self.isbn}"
            )
        else:
            return True

        data = {}
        try:
            data = requests.get(search_url).json()
        except requests.exceptions.ConnectionError:
            return False

        if "error" in data and data["error"]["status"] == "RESOURCE_EXHAUSTED":
            return False

        if "volumeInfo" in data:
            volume = data["volumeInfo"]
        elif "items" in data and data["items"]:
            volume = data["items"][0]["volumeInfo"]
            if "id" in data["items"][0] and not self.google_books_id:
                self.google_books_id = data["items"][0]["id"]
        else:
            return True

        if "publisher" in volume and not self.publisher:
            self.publisher = volume["publisher"]
            self.tags.append("updated-from-google")
        if "pageCount" in volume and not self.page_count:
            self.page_count = volume["pageCount"]
            self.tags.append("updated-from-google")
        if "publishedDate" in volume and not self.first_published:
            try:
                self.first_published = int(volume["publishedDate"].split("-")[0])
                self.tags.append("updated-from-google")
            except ValueError:
                pass

        self.save()
        return True

    @property
    def created_date_date(self) -> date:
        return self.created_date.date()


class BookAuthor(models.Model):
    class Meta:
        ordering = ["order"]
        unique_together = ("author", "book")

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    role = models.CharField(db_index=True, max_length=255, blank=True, default="")
    order = models.PositiveSmallIntegerField(db_index=True, blank=True, null=True)

    created_date = models.DateTimeField(db_index=True, default=timezone.now)
    modified_date = models.DateTimeField(db_index=True, default=timezone.now)

    def __str__(self) -> str:
        return ": ".join([str(self.author), str(self.role), self.book.title])


class TagManager(models.Manager):  # type: ignore [type-arg]
    def __getitem__(self, name: str) -> "Tag":  # type: ignore [override]
        return Tag.objects.get(name=name)


class Tag(models.Model):
    objects = TagManager()

    class Meta:
        ordering = ("name",)

    name = models.CharField(max_length=64, primary_key=True)
    parents = models.ManyToManyField(
        "self", related_name="children", blank=True, symmetrical=False
    )

    created_date = models.DateTimeField(db_index=True, default=timezone.now)
    modified_date = models.DateTimeField(db_index=True, default=timezone.now)

    def __str__(self) -> str:
        return self.fullname

    @property
    def fullname(self) -> str:
        if parent := self.parents.first():
            return parent.fullname + " :: " + self.name
        else:
            return self.name

    @property
    def books(self) -> "models.Manager[Book]":
        return Book.objects.filter(tags__contains=[self.name]).distinct()

    @property
    def books_recursive(self) -> "models.Manager[Book]":
        books = self.books
        for child in self.children.all():
            books |= child.books_recursive
        return books

    @property
    def books_uniquely_tagged(self) -> "models.Manager[Book]":
        return Book.objects.filter(
            Q(tags=[self.name])
            | Q(tags=sorted(["fiction", self.name]))
            | Q(tags=sorted(["non-fiction", self.name]))
        )

    def rename(self, new_name: str) -> None:
        new_tag, created = Tag.objects.get_or_create(name=new_name)
        new_tag.save()
        if created:
            for parent in self.parents:
                new_tag.parents.add(parent)
            new_tag.save()

        for book in self.books:
            book.tags.append(new_name)
            book.save()
        self.delete()

    def delete(self, *args: Any, **kwargs: Any) -> Tuple[int, Dict[str, int]]:
        for book in self.books:
            book.tags.remove(self.name)
            book.save()
        return super().delete(*args, **kwargs)


signals.pre_save.connect(receiver=update_timestamp_on_save, sender=Book)
signals.pre_save.connect(receiver=update_timestamp_on_save, sender=BookAuthor)
signals.pre_save.connect(receiver=update_timestamp_on_save, sender=Tag)
