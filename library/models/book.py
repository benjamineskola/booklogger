import operator
import re
import time
from datetime import date
from functools import reduce
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import quote

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from django.db import models
from django.db.models import Case, CheckConstraint, F, Q, Sum, Value, When
from django.db.models.functions import Lower
from django.db.models.indexes import Index
from django.urls import reverse
from django.utils import timezone

from library.models.abc import SluggableModel, TimestampedModel
from library.utils import (
    LANGUAGES,
    clean_publisher,
    goodreads,
    google,
    isbn_to_isbn10,
    oxford_comma,
    remove_stopwords,
    smarten,
    str2bool,
    verso,
)

from .author import Author

if TYPE_CHECKING:
    from .log_entry import LogEntry


class BaseBookManager(models.Manager["Book"]):
    def search(self, pattern: str) -> "BookQuerySet":
        qs: BookQuerySet = (
            self.annotate(  # type: ignore [assignment]
                first_author_similarity=TrigramSimilarity(
                    "first_author__surname", pattern
                ),
                other_author_similarity=TrigramSimilarity(
                    "additional_authors__surname", pattern
                ),
                title_similarity=TrigramSimilarity("title", pattern),
                subtitle_similarity=TrigramSimilarity("subtitle", pattern),
                series_similarity=TrigramSimilarity("series", pattern),
                edition_title_similarity=TrigramSimilarity("edition_title", pattern),
                edition_subtitle_similarity=TrigramSimilarity(
                    "edition_subtitle", pattern
                ),
                review_similarity=TrigramSimilarity("review", pattern),
                tags_similarity=SearchRank(SearchVector("tags"), SearchQuery(pattern)),
                similarity=(
                    F("first_author_similarity")
                    + Case(
                        When(Q(other_author_similarity__isnull=True), then=Value(0.0)),
                        default=F("other_author_similarity"),
                    )
                    + Case(
                        When(
                            Q(edition_title=""),
                            then=(
                                F("title_similarity") * 2 + F("subtitle_similarity") * 2
                            ),
                        ),
                        default=(
                            F("title_similarity")
                            + F("subtitle_similarity")
                            + F("edition_title_similarity")
                            + F("edition_subtitle_similarity")
                        ),
                    )
                    + F("series_similarity")
                    + F("review_similarity")
                    + F("tags_similarity") * 10
                ),
            )
            .order_by("-similarity")
            .filter(similarity__gt=0.2)
            .distinct()
        )
        return qs

    def regenerate_all_slugs(self) -> None:
        qs = self.get_queryset()
        qs.update(slug="")
        for book in qs:
            book.regenerate_slug()

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


class BookQuerySet(models.QuerySet["Book"]):
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
        return self.exclude(
            Q(log_entries__end_date__isnull=False)
            | Q(parent_edition__log_entries__end_date__isnull=False)
        ).distinct()

    def owned(self) -> "BookQuerySet":
        return self.owned_by("ben")

    def owned_by(self, user: str) -> "BookQuerySet":
        return self.filter(owned_by__username=user)

    def owned_by_any(self) -> "BookQuerySet":
        return self.filter(owned_by__isnull=False)

    def available(self) -> "BookQuerySet":
        return (
            self.filter(
                Q(owned_by__username="ben")
                | Q(parent_edition__owned_by__username="ben")
                # I can't make this recurse but three levels is the most I can fpresee needing
                | Q(parent_edition__parent_edition__owned_by__username="ben")
            )
            | self.borrowed()
        )

    def borrowed(self) -> "BookQuerySet":
        return self.exclude(owned_by=None).unowned() | self.filter(was_borrowed=True)

    def unowned(self) -> "BookQuerySet":
        return self.filter(
            owned_by__isnull=True,
            parent_edition__owned_by__isnull=True,
            parent_edition__parent_edition__owned_by__isnull=True,
        )

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
                if str2bool(owned):
                    qs = qs.owned()
                else:
                    qs = qs.unowned()
            except ValueError:
                if owned == "borrowed":
                    qs = qs.borrowed()
                elif owned == "available":
                    qs = qs.available()
                else:
                    qs = qs.owned_by(owned)
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
        return 0


BookManager = BaseBookManager.from_queryset(BookQuerySet)


class Book(TimestampedModel, SluggableModel):
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
        constraints = [
            CheckConstraint(
                check=(
                    Q(
                        # case one: both dates are set, so owner must not be set
                        acquired_date__isnull=False,
                        alienated_date__isnull=False,
                        owned_by__isnull=True,
                    )
                    | Q(
                        # case two: neither date is set, so owner must not be set
                        acquired_date__isnull=True,
                        alienated_date__isnull=True,
                        owned_by__isnull=True,
                    )
                    | Q(
                        # case three: acquired but not alienated so must have an owner
                        acquired_date__isnull=False,
                        alienated_date__isnull=True,
                        owned_by__isnull=False,
                    )
                    | Q(
                        # fallback case: neither date is set but might still be owned
                        acquired_date__isnull=True,
                        alienated_date__isnull=True,
                        owned_by__isnull=False,
                    )
                    | Q(
                        # default: neither date is set and it is not owned
                        acquired_date__isnull=True,
                        alienated_date__isnull=True,
                        owned_by__isnull=True,
                    )
                ),
                name="owned_dates_requires_owner",
            ),
            CheckConstraint(
                check=(
                    Q(owned_by__isnull=False, edition_format__ne=0)
                    | Q(owned_by__isnull=True, edition_format__gte=0)
                ),
                name="owned_must_have_format",
            ),
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
        choices=[(i / 2, i / 2) for i in range(0, 11)],
        blank=True,
        default=0,
    )

    has_ebook_edition = models.BooleanField(default=False)
    ebook_isbn = models.CharField(max_length=13, blank=True)
    ebook_asin = models.CharField(max_length=255, blank=True)
    ebook_acquired_date = models.DateField(blank=True, null=True)

    editions = models.ManyToManyField("self", symmetrical=True, blank=True)

    parent_edition = models.ForeignKey(
        "self",
        related_name="subeditions",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    private = models.BooleanField(db_index=True, default=False)

    def __str__(self) -> str:
        result = f"{self.first_author}, {self.display_title}"

        if (
            self.editions.count()
            and self.edition_format
            and self.edition_title
            in self.editions.all().values_list("edition_title", flat=True)
        ):
            result += f" ({self.get_edition_disambiguator()} edition)"
        return result

    @property
    def display_details(self) -> str:
        if len(self.authors) > 3:
            result = str(self.first_author) + " and others"
        else:
            result = oxford_comma([str(author) for author in self.authors])

        result += ", *" + self.display_title.replace("*", r"\*") + "*"

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
            return self.get_language_display()
        return self.get_edition_format_display().lower()

    def get_absolute_url(self) -> str:
        return reverse("library:book_details", args=[self.slug])

    @property
    def authors(self) -> list[Author]:
        additional_authors = list(
            self.additional_authors.filter(
                bookauthor__role=self.first_author_role
            ).order_by("bookauthor__order")
        )
        if self.first_author:
            return [self.first_author] + additional_authors
        return additional_authors

    @property
    def all_authors(self) -> list[Author]:
        additional_authors = list(self.additional_authors.order_by("bookauthor__order"))
        if self.first_author:
            return [self.first_author] + additional_authors
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
        return self.title + (": " + self.subtitle if self.subtitle else "")

    @property
    def display_date(self) -> str:
        if (
            self.edition_published
            and self.first_published
            and self.edition_published != self.first_published
        ):
            return f"[{self.first_published}] {self.edition_published}"
        if self.edition_published:
            return str(self.edition_published)
        if self.first_published:
            return str(self.first_published)
        return "n.d."

    @property
    def note_title(self) -> str:
        title = ""
        for author in self.authors:
            if len(self.authors) > 1 and author == self.authors[-1]:
                title += "and "
            title += author.name_sortable
            if len(self.authors) > 1 and author != self.authors[-1]:
                title += ", "

        title += f" ({self.first_published}), "

        if self.edition_title:
            title += self.edition_title.replace(":", ",")
        else:
            title += self.title.replace(":", ",")

        return title

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
            if not self.page_count:
                raise ValueError("Must specify percentage when page count is unset")
            percentage = page / self.page_count * 100

        entry = self.log_entries.get(end_date=None)
        entry.progress_date = timezone.now()

        entry.progress_page = page or 0
        entry.progress_percentage = percentage
        entry.save()
        return percentage

    def mark_read_sometime(self) -> None:
        self.log_entries.create(
            start_date=None, end_date="0001-01-01 00:00", end_precision=2
        )

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
        return bool(entries[0].currently_reading)

    @property
    def display_series(self) -> str:
        if not self.series:
            return ""
        if self.series_order:
            return f"{self.series}, #{str(self.series_order).replace('.0', '')}"
        return self.series

    @property
    def read(self) -> bool:
        if self.parent_edition and self.parent_edition.read:
            return True

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
        if not self.rating:
            self.rating = 0.0

        self.tags = sorted(
            {tag.lower().replace(",", "").replace("/", "").strip() for tag in self.tags}
        )
        for tag in self.tags:
            Tag.objects.get_or_create(name=tag)

        self.title = smarten(self.title)
        self.subtitle = smarten(self.subtitle)
        self.series = smarten(self.series)
        self.edition_title = smarten(self.edition_title)
        self.edition_subtitle = smarten(self.edition_subtitle)

        self.publisher = clean_publisher(self.publisher)

        if self.acquired_date and not self.alienated_date and not self.owned_by:
            self.owned_by = User.objects.get(username="ben")

        orig_goodreads_id = self.goodreads_id
        if self.id and (self.isbn or self.asin):
            old = Book.objects.get(pk=self.id)
            if self.isbn != old.isbn or self.asin != old.asin:
                self.goodreads_id = ""

        super().save(*args, **kwargs)

        self.update_from_verso()
        if any([self.asin, self.isbn, (self.title and self.first_author)]) and (
            not all([self.first_published, self.goodreads_id, self.image_url])
        ):
            self.update_from_goodreads()
            if orig_goodreads_id and not self.goodreads_id:
                self.goodreads_id = orig_goodreads_id
                super().save(*args, **kwargs)

        if any([self.isbn, self.google_books_id]) and (
            not all(
                [
                    self.google_books_id,
                    self.publisher,
                    self.page_count,
                    self.first_published,
                ]
            )
        ):
            self.update_from_google()
            self.update_from_verso()

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

    def _slug_fields(self) -> list[str]:
        fields = []
        if self.first_author:
            fields.append(self.first_author.surname)
        title = self.display_title.split(":")[0]

        title = remove_stopwords(title)

        fields.append(title)
        return fields

    @property
    def isbn10(self) -> str:
        return isbn_to_isbn10(self.isbn)

    @property
    def owned(self) -> bool:
        return (
            self.owned_by.username == "ben"
            if self.owned_by is not None
            else any((ancestor.owned for ancestor in self.ancestor_editions))
        )

    @property
    def owned_by_sara(self) -> bool:
        return (
            self.owned_by.username == "sara"
            if self.owned_by is not None
            else any((ancestor.owned_by_sara for ancestor in self.ancestor_editions))
        )

    @property
    def parent_owned(self) -> bool:
        return (not self.owned_by) and any(
            ancestor.owned for ancestor in self.ancestor_editions
        )

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
        data = google.fetch(self.google_books_id, self.isbn)
        if data is not None:
            self.update(data)
            return True
        return False

    def update_from_goodreads(
        self, data: Optional[dict[str, Any]] = None
    ) -> Optional["Book"]:
        result: Optional[dict[str, Any]]
        if data:
            result = data
        else:
            result = {}
            for query in [self.asin, self.isbn, self.search_query]:
                if query and (
                    result := goodreads.find(
                        query, self.first_author.surname if self.first_author else ""
                    )
                ):
                    break

            if not result:
                return None

        self.update(result)

        return self

    def update_from_verso(self) -> "Book":
        if self.publisher != "Verso":
            return self
        if self.publisher_url and "versobooks.com" in self.image_url:
            return self

        title = re.sub(
            r"[^A-Za-z0-9 -]+",
            " ",
            self.edition_title if self.edition_title else self.title,
        )
        title, *_ = title.split(": ", 1)

        url = (
            self.publisher_url
            if self.publisher_url
            else verso.find_page([self.search_query, title, str(self.first_author)])
        )
        if url:
            self.update({"publisher_url": url, "image_url": verso.scrape_image(url)})
        return self

    def update(self, data: dict[str, str], force: bool = False) -> "Book":
        needs_save = False

        for key, value in data.items():
            if key == "id":
                continue

            if hasattr(self, key) and (force or not getattr(self, key)):
                if value != getattr(self, key):
                    needs_save = True
                setattr(self, key, value)

        if needs_save:
            self.save()
        return self

    @property
    def created_date_date(self) -> date:
        return self.created_date.date()

    @property
    def modified_date_date(self) -> date:
        return self.modified_date.date()

    @property
    def ancestor_editions(self) -> list["Book"]:
        return (
            [self.parent_edition] + self.parent_edition.ancestor_editions
            if self.parent_edition
            else []
        )

    @property
    def review_url(self) -> str:
        if self.review.startswith("http://") or self.review.startswith("https://"):
            return self.review.split()[0]
        return ""


class BookAuthor(TimestampedModel):
    class Meta:
        ordering = ["order"]
        unique_together = ("author", "book")

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    role = models.CharField(db_index=True, max_length=255, blank=True, default="")
    order = models.PositiveSmallIntegerField(db_index=True, blank=True, null=True)

    def __str__(self) -> str:
        return ": ".join([str(self.author), str(self.role), self.book.title])


class TagManager(models.Manager["Tag"]):
    def __getitem__(self, name: str) -> "Tag":
        return Tag.objects.get(name=name)


class Tag(TimestampedModel):
    objects = TagManager()

    class Meta:
        ordering = ("name",)

    name = models.CharField(max_length=64, primary_key=True)
    parents = models.ManyToManyField(
        "self", related_name="children", blank=True, symmetrical=False
    )

    def __str__(self) -> str:
        return self.fullname

    @property
    def fullname(self) -> str:
        if parent := self.parents.first():
            return parent.fullname + " :: " + self.name
        return self.name

    @property
    def books(self) -> "BookQuerySet":
        return Book.objects.filter(tags__contains=[self.name]).distinct()

    @property
    def books_recursive(self) -> "BookQuerySet":
        books = self.books
        for child in self.children.all():
            books |= child.books_recursive
        return books

    @property
    def books_uniquely_tagged(self) -> "BookQuerySet":
        return Book.objects.filter(
            Q(tags=[self.name])
            | Q(tags=sorted(["fiction", self.name]))
            | Q(tags=sorted(["non-fiction", self.name]))
        )

    @property
    def parents_recursive(self) -> models.QuerySet["Tag"]:
        return reduce(
            operator.or_,
            [p.parents_recursive for p in self.parents.all()],
            self.parents.all(),
        )

    @property
    def children_recursive(self) -> models.QuerySet["Tag"]:
        return reduce(
            operator.or_,
            [c.children_recursive for c in self.children.all()],
            self.children.all(),
        )

    @property
    def related(self) -> models.QuerySet["Tag"]:
        return reduce(
            operator.or_,
            [Tag.objects.filter(name__in=book.tags) for book in self.books.all()],
        )

    def __lt__(self, other: "Tag") -> bool:
        return self.name < other.name

    def get_absolute_url(self) -> str:
        return reverse("library:tag_details", args=[self.name])

    def rename(self, new_name: str) -> None:
        new_tag, created = Tag.objects.get_or_create(name=new_name)
        new_tag.save()
        if created:
            for parent in self.parents.all():
                new_tag.parents.add(parent)
            new_tag.save()

        for book in self.books:
            book.tags.append(new_name)
            book.save()
        self.delete()

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        for book in self.books:
            book.tags.remove(self.name)
            book.save()
        return super().delete(*args, **kwargs)
