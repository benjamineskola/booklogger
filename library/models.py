import re
import string

from django.db import models
from django.db.models.functions import Lower

# Create your models here.


class Author(models.Model):
    surname = models.CharField(max_length=255)
    forenames = models.CharField(max_length=255)

    class Gender(models.IntegerChoices):
        UNKNOWN = 0
        MALE = 1
        FEMALE = 2
        ORGANIZATION = 3

    gender = models.IntegerField(choices=Gender.choices, default=0)

    def __str__(self):
        return f"{self.surname}{', ' + self.initials if self.initials else ''}"

    def attribution_for(self, book):
        role = self._role_for_book(book)
        return str(self) + (f" ({role})" if role else "")

    def _role_for_book(self, book):
        if (rel := self.bookauthor_set.get(book=book.id)) and rel.role:
            role = "ed." if rel.role == "editor" else rel.role
            return role

    @property
    def initials(self):
        if not self.forenames:
            return ""
        all_forenames = re.split(r"[. ]+", self.forenames)
        return ".".join([name[0] for name in all_forenames if name]) + "."


class Book(models.Model):
    class Meta:
        ordering = [
            Lower("authors__surname"),
            Lower("authors__forenames"),
            "series",
            "series_order",
            "title",
        ]

    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    authors = models.ManyToManyField(Author, through="BookAuthor", related_name="books")

    class Format(models.IntegerChoices):
        PAPERBACK = 1
        HARDBACK = 2
        EBOOK = 3
        WEB = 4

    first_published = models.PositiveSmallIntegerField(blank=True, null=True)
    language = models.CharField(max_length=2, default="en")

    series = models.CharField(max_length=255, blank=True)
    series_order = models.FloatField(blank=True, null=True)

    # these at least in theory relate only to an edition, not every edition
    # edition could be a separate models but it would almost always be one-to-one
    edition_published = models.PositiveSmallIntegerField(blank=True, null=True)
    publisher = models.CharField(max_length=255, blank=True)
    edition_format = models.IntegerField(choices=Format.choices, blank=True, null=True)
    edition_number = models.PositiveSmallIntegerField(blank=True, null=True)
    page_count = models.PositiveSmallIntegerField(blank=True, null=True)
    goodreads_id = models.CharField(max_length=255, blank=True)
    google_books_id = models.CharField(max_length=255, blank=True)
    isbn = models.CharField(max_length=13, blank=True)
    asin = models.CharField(max_length=255, blank=True)
    edition_language = models.CharField(max_length=2, blank=True)  # i.e., a translation
    edition_title = models.CharField(max_length=255, blank=True)  # if translated
    edition_subtitle = models.CharField(max_length=255, blank=True)  # if translated

    owned = models.BooleanField(default=False)
    acquired_date = models.DateField(blank=True, null=True)
    alienated_date = models.DateField(blank=True, null=True)
    was_borrowed = models.BooleanField(default=False)
    borrowed_from = models.CharField(max_length=255, blank=True)

    image_url = models.URLField(blank=True)
    publisher_url = models.URLField(blank=True)

    def __str__(self):
        return (
            self.all_authors
            + ", "
            + self.display_title
            + (f" ({self.series}, #{self.series_order})" if self.series else "")
        )

    @property
    def all_authors(self):
        return " and ".join([a.attribution_for(self) for a in self.authors.all()])

    @property
    def display_title(self):
        return self.edition_title if self.edition_title else self.title

    @property
    def authors_with_roles(self):
        return [(a.attribution_for(self), a.id) for a in self.authors.all()]

    def add_author(self, author, role="", order=None):
        authorship = BookAuthor(book=self, author=author, role=role, order=order)
        authorship.save()


class BookAuthor(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    role = models.CharField(max_length=255)
    order = models.PositiveSmallIntegerField(blank=True, null=True)
