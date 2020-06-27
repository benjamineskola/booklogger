import os
import re
from typing import Any, Dict, Iterable, Optional, Sequence

import requests
import xmltodict
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.db.models.indexes import Index
from django.urls import reverse
from django.utils import timezone

from library.utils import oxford_comma

from .author import Author

LogEntry = models.Model


class BookManager(models.Manager):  # type: ignore [type-arg]
    def get_queryset(self) -> "BookQuerySet":
        return BookQuerySet(self.model, using=self._db)

    def by_gender(self, gender: int) -> "BookQuerySet":
        return self.get_queryset().by_gender(gender)

    def by_men(self) -> "BookQuerySet":
        return self.get_queryset().by_men()

    def by_women(self) -> "BookQuerySet":
        return self.get_queryset().by_women()

    def fiction(self) -> "BookQuerySet":
        return self.get_queryset().fiction()

    def nonfiction(self) -> "BookQuerySet":
        return self.get_queryset().nonfiction()

    def search(self, pattern: str) -> "BookQuerySet":
        query = SearchQuery(pattern)
        vector = SearchVector(
            "title",
            "series",
            "tags",
            "edition_title",
            "first_author__surname",
            "first_author__forenames",
            "additional_authors__surname",
            "additional_authors__forenames",
        )

        return (
            self.annotate(rank=SearchRank(vector, query))
            .filter(rank__gte=0.01)
            .order_by("-rank")
        ).distinct()  # type: ignore [return-value]

    def rename_tag(self, old_name: str, new_name: str) -> None:
        tagged_books = self.filter(tags__contains=[old_name])
        for book in tagged_books:
            book.tags.append(new_name)
            book.tags.remove(old_name)
            book.save()

    def filter_by_request(self, request: str) -> "BookQuerySet":
        return self.get_queryset().filter_by_request(request)

    def find_on_goodreads(self, query: str) -> Optional[Dict[str, Any]]:
        search_url = f"https://www.goodreads.com/search/index.xml?key={os.environ['GOODREADS_KEY']}&q={query}"
        data = requests.get(search_url).text
        xml = xmltodict.parse(data, dict_constructor=dict)

        try:
            all_results = xml["GoodreadsResponse"]["search"]["results"]["work"]
        except:
            return None

        results: Sequence[Dict[str, Any]] = []
        if "id" in all_results:
            results = [all_results]
        else:
            results = all_results

        return results[0]

    def create_from_goodreads(self, query: str) -> Optional["Book"]:
        result = self.find_on_goodreads(query)
        if not result:
            return None

        goodreads_book = result["best_book"]
        book = Book(
            title=goodreads_book["title"],
            goodreads_id=goodreads_book["id"]["#text"],
            first_published=result["original_publication_year"]["#text"],
        )

        if not "nophoto" in goodreads_book["image_url"]:
            book.image_url = re.sub(
                r"_S\w\d+_.jpg$", "_SX475_.jpg", goodreads_book["image_url"]
            )

        book.first_author, created = Author.objects.get_or_create_by_single_name(
            goodreads_book["author"]["name"]
        )
        book.save()

        return book


class BookQuerySet(models.QuerySet):  # type: ignore [type-arg]
    def by_gender(self, gender: int) -> "BookQuerySet":
        return (
            self.filter(first_author__gender=gender).distinct()
            | self.filter(additional_authors__gender=gender).distinct()
        )

    def by_men(self) -> "BookQuerySet":
        return self.by_gender(1)

    def by_women(self) -> "BookQuerySet":
        return self.by_gender(2)

    def fiction(self) -> "BookQuerySet":
        return self.filter(tags__contains=["fiction"])

    def nonfiction(self) -> "BookQuerySet":
        return self.filter(tags__contains=["non-fiction"])

    def filter_by_request(self, request: Any) -> "BookQuerySet":
        filter_by = Q()
        if gender := request.GET.get("gender"):
            if not gender.isdigit():
                gender = Author.Gender[gender.upper()]
            filter_by &= Q(first_author__gender=gender) | Q(
                additional_authors__gender=gender
            )
        if poc := request.GET.get("poc"):
            filter_by &= Q(first_author__poc=bool(int(poc))) | Q(
                additional_authors__poc=bool(int(poc))
            )
        if tags := request.GET.get("tags"):
            filter_by &= Q(
                tags__contains=[tag.strip().lower() for tag in tags.split(",")]
            )

        return self.filter(filter_by)


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
        Author, through="BookAuthor", related_name="additional_authored_books"
    )

    class Format(models.IntegerChoices):
        UNKNOWN = 0
        PAPERBACK = 1
        HARDBACK = 2
        EBOOK = 3
        WEB = 4

    LANGUAGES = sorted(set([(x, y) for x, y in settings.LANGUAGES if len(x) == 2]))

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

    owned = models.BooleanField(db_index=True, default=False)
    acquired_date = models.DateField(blank=True, null=True)
    alienated_date = models.DateField(blank=True, null=True)
    was_borrowed = models.BooleanField(db_index=True, default=False)
    borrowed_from = models.CharField(max_length=255, blank=True)

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

    editions = models.ManyToManyField("self", symmetrical=True, blank=True)

    def __str__(self) -> str:
        if self.editions.all() and self.edition_format:
            return (
                self.citation
                + f" ({self.get_edition_format_display().lower()} edition)"
            )
        else:
            return self.citation

    def get_absolute_url(self) -> str:
        return reverse("library:book_details", args=[str(self.id)])

    def get_link_data(self, **kwargs: Dict[str, Any]) -> Dict[str, str]:
        return {"url": self.get_absolute_url(), "text": self.display_title}

    @property
    def all_authors(self) -> Sequence[Author]:
        authors = []
        if self.first_author:
            authors.append(self.first_author)
        if self.additional_authors.count():
            authors += [ba.author for ba in self.bookauthor_set.all()]

        return authors

    @property
    def authors(self) -> Sequence[Author]:
        authors = []
        if self.first_author:
            authors.append(self.first_author)
        if self.additional_authors.count():
            authors += [
                ba.author
                for ba in self.bookauthor_set.filter(role=self.first_author_role)
            ]
        return authors

    @property
    def all_authors_editors(self) -> bool:
        if len(self.authors) > 1:
            attributions = [author._role_for_book(self) for author in self.authors]
            if set(attributions) == {"ed."}:
                return True
        return False

    @property
    def display_authors(self) -> str:
        if len(self.authors) > 3:
            return str(self.authors[0].attribution_for(self)) + " and others"
        elif self.all_authors_editors:
            return (
                oxford_comma([author.name_with_initials for author in self.authors])
                + " (eds.)"
            )
        else:
            return oxford_comma(
                [a.attribution_for(self, initials=True) for a in self.authors]
            )

    @property
    def display_title(self) -> str:
        return self.edition_title if self.edition_title else self.title

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

    @property
    def citation(self) -> str:
        citation = f"{self.display_authors} ({self.display_date}) {self.display_title}."
        if self.publisher:
            citation += f" {self.publisher}."
        return citation

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
        entry.end_date = timezone.now()
        entry.progress_date = timezone.now()
        entry.progress = 100
        entry.save()

    def update_progress(self, progress: int) -> None:
        entry = self.log_entries.get(end_date=None)
        entry.progress_date = timezone.now()
        entry.progress = progress
        entry.save()

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
        if not self.log_entries.count():
            return False
        completed_entries = [
            entry.end_date for entry in self.log_entries.all() if entry.end_date
        ]
        return bool(completed_entries)

    @property
    def slug(self) -> str:
        if self.first_author:
            name = self.first_author.surname + "-"
        else:
            name = ""

        name += self.title.split(":")[0]
        return re.sub(r"[^A-Za-z0-9]+", "-", name,).lower()

    def add_tags(self, tags: Iterable[str]) -> None:
        for tag in tags:
            clean_tag = tag.strip().lower()
            if not clean_tag in self.tags:
                self.tags.append(clean_tag)
        self.save()

        for edition in self.editions.all():
            edition.add_tags(tags)

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

    @property
    def all_log_entries(self) -> "models.QuerySet[LogEntry]":
        entries = self.log_entries.all()
        for edition in self.editions.all():
            entries |= edition.log_entries.all()
        return entries


class BookAuthor(models.Model):
    class Meta:
        ordering = ["order"]
        unique_together = ("author", "book")

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    role = models.CharField(db_index=True, max_length=255, blank=True, default="")
    order = models.PositiveSmallIntegerField(db_index=True, blank=True, null=True)

    def __str__(self) -> str:
        return ": ".join([str(self.author), str(self.role), self.book.title])

    @property
    def display_role(self) -> str:
        return "ed." if self.role == "editor" else self.role
