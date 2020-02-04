import re

from django.contrib.postgres.search import TrigramDistance
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.db.models.indexes import Index


class AuthorManager(models.Manager):
    def search(self, pattern):
        return Author.objects.annotate(
            sn_distance=TrigramDistance("surname", pattern),
            fn_distance=TrigramDistance("forenames", pattern),
            distance=F("sn_distance") * F("fn_distance"),
        ).order_by("distance")


class Author(models.Model):
    objects = AuthorManager()

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
        if book.first_author == self:
            return (
                "ed." if book.first_author_role == "editor" else book.first_author_role
            )
        elif rel := self.bookauthor_set.get(book=book.id):
            return rel.display_role

    @property
    def initials(self):
        if not self.forenames:
            return ""
        all_forenames = re.split(r"[. ]+", self.forenames)
        return ".".join([name[0] for name in all_forenames if name]) + "."

    @property
    def authored_books(self):
        books = self.books.filter(
            id__in=[
                ba.book.id
                for ba in self.bookauthor_set.filter(
                    Q(role__isnull=True) | Q(role="") | Q(role="author")
                )
            ]
        )
        return books

    @property
    def edited_books(self):
        books = self.books.filter(
            id__in=[ba.book.id for ba in self.bookauthor_set.filter(role="editor")]
        )
        return books
