import re

from django.contrib.postgres.search import TrigramDistance
from django.db import models
from django.db.models import CheckConstraint, F, Q
from django.db.models.functions import Lower
from django.db.models.indexes import Index
from django.urls import reverse


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
        constraints = [
            CheckConstraint(
                check=(
                    (Q(surname="") & Q(forenames="") & ~Q(single_name=""))
                    | (~Q(surname="") & ~Q(forenames="") & Q(single_name=""))
                ),
                name="surname_and_forenames_or_single_name",
            )
        ]
        indexes = [Index(fields=["surname", "forenames"])]
        ordering = [
            Lower("single_name"),
            Lower("surname"),
            Lower("forenames"),
        ]

    surname = models.CharField(db_index=True, max_length=255, blank=True)
    forenames = models.CharField(db_index=True, max_length=255, blank=True)
    single_name = models.CharField(db_index=True, max_length=255, blank=True)

    class Gender(models.IntegerChoices):
        UNKNOWN = 0
        MALE = 1
        FEMALE = 2
        ORGANIZATION = 3

    gender = models.IntegerField(choices=Gender.choices, default=0)
    poc = models.BooleanField(default=False)

    def __str__(self):
        if self.single_name:
            return self.single_name
        else:
            return " ".join([self.forenames, self.surname]).strip()

    @property
    def name_with_initials(self):
        if self.single_name:
            return self.single_name
        else:
            return self.surname + ", " + self.initials

    def get_absolute_url(self):
        return reverse("library:author_details", args=[str(self.id)])

    def get_link_data(self, book=None, **kwargs):
        return {
            "url": self.get_absolute_url(),
            "text": self.attribution_for(book, initials=False) if book else str(self),
        }

    def attribution_for(self, book, initials=False):
        role = self._role_for_book(book)
        if initials:
            name = self.name_with_initials
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
    def books(self):
        return (
            self.first_authored_books.all() | self.additional_authored_books.all()
        ).distinct()

    @property
    def authored_books(self):
        books = (
            self.books.filter(
                id__in=[
                    ba.book.id
                    for ba in self.bookauthor_set.filter(Q(role="") | Q(role="author"))
                ]
            )
            | self.first_authored_books.filter(
                Q(first_author_role="") | Q(first_author_role="author")
            ).distinct()
        )
        return books

    @property
    def edited_books(self):
        books = (
            self.books.filter(
                id__in=[ba.book.id for ba in self.bookauthor_set.filter(role="editor")]
            )
            | self.first_authored_books.filter(first_author_role="editor").distinct()
        )
        return books
