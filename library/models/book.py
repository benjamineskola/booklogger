from django.contrib.postgres.search import TrigramDistance
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.db.models.indexes import Index
from django.utils import timezone

from library.utils import oxford_comma

from .author import Author


class BookManager(models.Manager):
    def search(self, pattern):
        return Book.objects.annotate(
            title_distance=TrigramDistance("title", pattern),
            series_distance=TrigramDistance("series", pattern),
            distance=F("title_distance") * F("series_distance"),
        ).order_by("distance")


class Book(models.Model):
    objects = BookManager()

    class Meta:
        indexes = [Index(fields=["series", "series_order", "title"])]
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
        db_index=True, max_length=255, blank=True, null=True
    )
    additional_authors = models.ManyToManyField(
        Author, through="BookAuthor", related_name="additional_authored_books"
    )

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
    def authors(self):
        authors = []
        if self.first_author:
            authors.append(self.first_author)
        if self.additional_authors.count():
            authors += self.additional_authors.all()
        return authors

    @property
    def all_authors_attributed(self):
        return [a.attribution_for(self) for a in self.authors]

    @property
    def display_authors(self):
        return oxford_comma(self.all_authors_attributed)

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
            return f"{self.series}, #{str(self.series_order).strip('.0')}"
        else:
            return self.series


class BookAuthor(models.Model):
    class Meta:
        ordering = ["order"]
        unique_together = ("author", "book")

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    role = models.CharField(db_index=True, max_length=255, blank=True, null=True)
    order = models.PositiveSmallIntegerField(db_index=True, blank=True, null=True)

    def __str__(self):
        return ": ".join([str(self.author), str(self.role), self.book.title])

    @property
    def display_role(self):
        return "ed." if self.role == "editor" else self.role
