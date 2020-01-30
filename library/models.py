import re
import string
from datetime import date

from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.db.models.indexes import Index

from library.utils import oxford_comma

# Create your models here.


class Author(models.Model):
    class Meta:
        indexes = [Index(fields=["surname", "forenames"])]
        ordering = [
            Lower("surname"),
            Lower("forenames"),
        ]

    surname = models.CharField(db_index=True, max_length=255)
    forenames = models.CharField(db_index=True, max_length=255)

    class Gender(models.IntegerChoices):
        UNKNOWN = 0
        MALE = 1
        FEMALE = 2
        ORGANIZATION = 3

    gender = models.IntegerField(choices=Gender.choices, default=0)

    def __str__(self):
        return " ".join([self.forenames, self.surname]).strip()

    def attribution_for(self, book, initials=True):
        role = self._role_for_book(book)
        if initials:
            name = f"{self.surname}{', ' + self.initials if self.initials else ''}"
        else:
            name = str(self)
        return name + (f" ({role})" if role else "")

    def _role_for_book(self, book):
        if rel := self.bookauthor_set.get(book=book.id):
            return rel.display_role

    @property
    def initials(self):
        if not self.forenames:
            return ""
        all_forenames = re.split(r"[. ]+", self.forenames)
        return ".".join([name[0] for name in all_forenames if name]) + "."


class Book(models.Model):
    class Meta:
        indexes = [Index(fields=["series", "series_order", "title"])]
        ordering = [
            Lower("authors__surname"),
            Lower("authors__forenames"),
            "series",
            "series_order",
            "title",
        ]

    title = models.CharField(db_index=True, max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    authors = models.ManyToManyField(Author, through="BookAuthor", related_name="books")

    class Format(models.IntegerChoices):
        PAPERBACK = 1
        HARDBACK = 2
        EBOOK = 3
        WEB = 4

    first_published = models.PositiveSmallIntegerField(blank=True, null=True)
    language = models.CharField(max_length=2, default="en")

    series = models.CharField(db_index=True, max_length=255, blank=True)
    series_order = models.FloatField(db_index=True, blank=True, null=True)

    # these at least in theory relate only to an edition, not every edition
    # edition could be a separate models but it would almost always be one-to-one
    edition_published = models.PositiveSmallIntegerField(blank=True, null=True)
    publisher = models.CharField(max_length=255, blank=True)
    edition_format = models.IntegerField(
        db_index=True, choices=Format.choices, blank=True, null=True
    )
    edition_number = models.PositiveSmallIntegerField(blank=True, null=True)
    page_count = models.PositiveSmallIntegerField(blank=True, null=True)
    goodreads_id = models.CharField(max_length=255, blank=True)
    google_books_id = models.CharField(max_length=255, blank=True)
    isbn = models.CharField(max_length=13, blank=True)
    asin = models.CharField(max_length=255, blank=True)
    edition_language = models.CharField(max_length=2, blank=True)  # i.e., a translation
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

    def __str__(self):
        return self.citation

    @property
    def all_authors(self):
        return [a.attribution_for(self) for a in self.default_authors]

    @property
    def display_authors(self):
        return oxford_comma(self.all_authors)

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
        if author not in self.authors.all():
            authorship = BookAuthor(book=self, author=author, role=role, order=order)
            authorship.save()

    def start_reading(self):
        if not self.log_entries.filter(end_date=None):
            self.log_entries.create()

    def finish_reading(self):
        entry = self.log_entries.get(end_date=None)
        entry.end_date = date.today()
        entry.save()

    @property
    def currently_reading(self):
        entries = self.log_entries.filter(end_date=None).order_by("-start_date")
        if not entries:
            return False
        else:
            return entries[0].currently_reading

    @property
    def normal_authors(self):
        return self.bookauthor_set.filter(
            Q(role__isnull=True) | Q(role="") | Q(role="author")
        )

    @property
    def editors(self):
        return self.bookauthor_set.filter(role="editor")

    @property
    def contributors(self):
        return self.bookauthor_set.filter(role="contributor")

    @property
    def default_authors(self):
        book_authors = []
        if self.normal_authors.count():
            book_authors = self.normal_authors
        elif self.editors.count():
            book_authors = self.editors

        return [book_author.author for book_author in book_authors.order_by("order")]

    @property
    def full_authors(self):
        return [
            book_author.author for book_author in self.bookauthor_set.order_by("order")
        ]


class BookAuthor(models.Model):
    class Meta:
        unique_together = ("author", "book")

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    role = models.CharField(max_length=255, blank=True, null=True)
    order = models.PositiveSmallIntegerField(blank=True, null=True)

    def __str__(self):
        return ": ".join([str(self.author), str(self.role), self.book.title])

    @property
    def display_role(self):
        return "ed." if self.role == "editor" else self.role


class LogEntry(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="log_entries")
    start_date = models.DateField(default=date.today, blank=True, null=True)
    end_date = models.DateField(db_index=True, blank=True, null=True)

    class DatePrecision(models.IntegerChoices):
        DAY = 0
        MONTH = 1
        YEAR = 2

    start_precision = models.PositiveSmallIntegerField(
        choices=DatePrecision.choices, default=0
    )
    end_precision = models.PositiveSmallIntegerField(
        choices=DatePrecision.choices, default=0
    )

    def __str__(self):
        return f"{self.book} from {self.start_date} to {self.end_date}"

    @property
    def currently_reading(self):
        if self.start_date and not self.end_date:
            return True
        else:
            return False

    @property
    def start_date_display(self):
        return self._date_with_precision(self.start_date, self.start_precision)

    @property
    def end_date_display(self):
        return self._date_with_precision(self.end_date, self.end_precision)

    def _date_with_precision(self, date, precision):
        if precision == 2:
            return date.strftime("%Y")
        elif precision == 1:
            return date.strftime("%B %Y")
        else:
            return date.strftime("%d %B, %Y")
