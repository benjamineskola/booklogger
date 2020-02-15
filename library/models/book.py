import os
import re

import requests
import xmltodict
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.db.models.indexes import Index
from django.urls import reverse
from django.utils import timezone

from library.utils import oxford_comma

from .author import Author


class BookManager(models.Manager):
    def get_queryset(self):
        return BookQuerySet(self.model, using=self._db)

    def by_gender(self, gender):
        return self.get_queryset().by_gender(gender)

    def by_men(self):
        return self.get_queryset().by_men()

    def by_women(self):
        return self.get_queryset().by_women()

    def fiction(self):
        return self.get_queryset().fiction()

    def nonfiction(self):
        return self.get_queryset().nonfiction()

    def search(self, pattern):
        query = SearchQuery(pattern)
        vector = SearchVector(
            "title",
            "series",
            "tags",
            "edition_title",
            "first_author__surname",
            "first_author__forenames",
            "first_author__single_name",
            "additional_authors__surname",
            "additional_authors__forenames",
            "additional_authors__single_name",
        )

        return (
            self.annotate(rank=SearchRank(vector, query))
            .filter(rank__gte=0.01)
            .order_by("-rank")
        ).distinct()

    def rename_tag(self, old_name, new_name):
        tagged_books = self.filter(tags__contains=[old_name])
        for book in tagged_books:
            book.tags.append(new_name)
            book.tags.remove(old_name)
            book.save()

    def filter_by_request(self, request):
        return self.get_queryset().filter_by_request(request)


class BookQuerySet(models.QuerySet):
    def by_gender(self, gender):
        return (
            self.filter(first_author__gender=gender).distinct()
            | self.filter(additional_authors__gender=gender).distinct()
        )

    def by_men(self):
        return self.by_gender(1)

    def by_women(self):
        return self.by_gender(2)

    def fiction(self):
        return self.filter(tags__contains=["fiction"])

    def nonfiction(self):
        return self.filter(tags__contains=["non-fiction"])

    def filter_by_request(self, request):
        filter_by = {}
        if gender := request.GET.get("gender"):
            if not gender.isdigit():
                gender = Author.Gender[gender.upper()]
            filter_by["first_author__gender"] = gender
        if poc := request.GET.get("poc"):
            filter_by["first_author__poc"] = bool(int(poc))
        if tags := request.GET.get("tags"):
            filter_by["tags__contains"] = [tag.strip() for tag in tags.split(",")]

        return self.filter(**filter_by)


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

    def __str__(self):
        return self.citation

    def get_absolute_url(self):
        return reverse("library:book_details", args=[str(self.id)])

    def get_link_data(self, **kwargs):
        return {"url": self.get_absolute_url(), "text": self.display_title}

    @property
    def all_authors(self):
        authors = []
        if self.first_author:
            authors.append(self.first_author)
        if self.additional_authors.count():
            authors += self.additional_authors.all()
        return authors

    @property
    def authors(self):
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
    def all_authors_editors(self):
        if len(self.authors) > 1:
            attributions = [author._role_for_book(self) for author in self.authors]
            if set(attributions) == {"ed."}:
                return True
        return False

    @property
    def display_authors(self):
        if self.all_authors_editors:
            return (
                oxford_comma([author.name_with_initials for author in self.authors])
                + " (eds.)"
            )
        else:
            return oxford_comma(
                [a.attribution_for(self, initials=True) for a in self.authors]
            )

    @property
    def display_title(self):
        return self.edition_title if self.edition_title else self.title

    @property
    def display_date(self):
        return (
            self.edition_published if self.edition_published else self.first_published
        )

    @property
    def citation(self):
        return " ".join(
            [
                self.display_authors + ",",
                self.display_title,
                (f"({self.publication_data})" if self.publication_data else ""),
            ]
        ).strip()

    @property
    def publication_data(self):
        return ", ".join([str(i) for i in [self.publisher, self.display_date] if i])

    def add_author(self, author, role="", order=None):
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

    def start_reading(self):
        if not self.log_entries.filter(end_date=None):
            self.log_entries.create()

    def finish_reading(self):
        entry = self.log_entries.get(end_date=None)
        entry.end_date = timezone.now()
        entry.progress_date = timezone.now()
        entry.progress = 100
        entry.save()

    def update_progress(self, progress):
        entry = self.log_entries.get(end_date=None)
        entry.progress_date = timezone.now()
        entry.progress = progress
        entry.save()

    @property
    def currently_reading(self):
        entries = self.log_entries.filter(end_date=None).order_by("-start_date")
        if not entries:
            return False
        else:
            return entries[0].currently_reading

    @property
    def display_series(self):
        if not self.series:
            return
        elif self.series_order:
            return f"{self.series}, #{str(self.series_order).replace('.0', '')}"
        else:
            return self.series

    @property
    def slug(self):
        return re.sub(
            r"[^A-Za-z0-9]+",
            "-",
            f"{self.first_author.surname} {self.title.split(':')[0]}",
        ).lower()

    def find_goodreads_data(self):
        query = ""
        if self.isbn:
            query = self.isbn
        else:
            query = re.sub(" ", "+", self.title + " " + str(self.first_author))
        search_url = f"https://www.goodreads.com/search/index.xml?key={os.environ['GOODREADS_KEY']}&q={query}"
        data = requests.get(search_url).text
        xml = xmltodict.parse(data, dict_constructor=dict)

        try:
            results = xml["GoodreadsResponse"]["search"]["results"]["work"]
        except:
            return
        if "id" in results:
            results = [results]

        for result in results:
            book = result["best_book"]
            full_title = book["title"].lower()
            title_without_series, *rest = full_title.split(" (")

            if (
                full_title != self.title.lower()
                and title_without_series != self.title.lower()
            ):
                continue
            if book["author"]["name"].lower() != str(self.first_author).lower():
                continue

            if not self.goodreads_id:
                self.goodreads_id = book["id"]["#text"]
            if not self.image_url:
                if not "nophoto" in book["image_url"]:
                    self.image_url = re.sub(
                        r"_S\w\d+_.jpg$", "_SX475_.jpg", book["image_url"]
                    )
            self.save()
            return


class BookAuthor(models.Model):
    class Meta:
        ordering = ["order"]
        unique_together = ("author", "book")

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    role = models.CharField(db_index=True, max_length=255, blank=True, default="")
    order = models.PositiveSmallIntegerField(db_index=True, blank=True, null=True)

    def __str__(self):
        return ": ".join([str(self.author), str(self.role), self.book.title])

    @property
    def display_role(self):
        return "ed." if self.role == "editor" else self.role
