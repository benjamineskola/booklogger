import re
from typing import TYPE_CHECKING, Any

from django.contrib.postgres.search import TrigramSimilarity
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.db.models.indexes import Index
from django.urls import reverse

from library.models.abc import SluggableModel, TimestampedModel
from library.utils import LANGUAGES, remove_stopwords

if TYPE_CHECKING:
    from .book import Book, BookQuerySet  # pragma: no cover


class AuthorManager(models.Manager["Author"]):
    def search(self, pattern: str) -> "models.QuerySet[Author]":
        return (
            Author.objects.annotate(
                sn_similarity=TrigramSimilarity("surname", pattern),
                fn_similarity=TrigramSimilarity("forenames", pattern),
                similarity=(F("sn_similarity") + F("fn_similarity")),
            )
            .order_by("-similarity")
            .filter(similarity__gt=0.25)
        )

    def get_by_single_name(self, name: str) -> "Author":
        names = Author.normalise_name(name)
        return Author.objects.get(
            Q(surname=name, forenames="")
            | Q(**names)
            | Q(surname=names["surname"], preferred_forenames=names["forenames"])
        )

    def get_or_create_by_single_name(self, name: str) -> tuple["Author", bool]:
        try:
            return (Author.objects.get_by_single_name(name), False)
        except self.model.DoesNotExist:
            return Author.objects.get_or_create(**Author.normalise_name(name))

    def regenerate_all_slugs(self) -> None:
        qs = self.get_queryset()
        qs.update(slug="")
        for author in qs:
            author.regenerate_slug()


class Author(TimestampedModel, SluggableModel):
    objects = AuthorManager()

    class Meta:
        indexes = [Index(fields=["surname", "forenames"])]
        ordering = [
            Lower("surname"),
            Lower("forenames"),
        ]

    surname = models.CharField(db_index=True, max_length=255)
    forenames = models.CharField(db_index=True, max_length=255, blank=True)
    preferred_forenames = models.CharField(db_index=True, max_length=255, blank=True)
    surname_first = models.BooleanField(default=False)

    class Gender(models.IntegerChoices):
        UNKNOWN = 0
        MALE = 1
        FEMALE = 2
        ORGANIZATION = 3
        NONBINARY = 4

    gender = models.IntegerField(choices=Gender.choices, default=0)
    poc = models.BooleanField(default=False)

    slug = models.SlugField(blank=True, default="")

    primary_language = models.CharField(max_length=2, default="en", choices=LANGUAGES)

    primary_identity = models.ForeignKey(
        "self",
        related_name="pseudonyms",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self) -> str:
        if not self.forenames:
            return self.surname

        return (
            f"{self.surname} " + (self.preferred_forenames or self.forenames)
            if self.surname_first
            else (self.preferred_forenames or self.forenames) + " " + self.surname
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "surname": self.surname,
            "forenames": self.forenames,
            "preferred_forenames": self.preferred_forenames,
            "surname_first": self.surname_first,
            "gender": self.gender,
            "poc": self.poc,
            "primary_language": self.primary_language,
            "primary_identity": self.primary_identity_id,
        }

    @property
    def full_name(self) -> str:
        if not self.forenames:
            return self.surname
        if self.surname_first:
            return f"{self.surname} {self.forenames}"
        return f"{self.forenames} {self.surname}"

    @property
    def name_with_initials(self) -> str:
        return f"{self.surname}, {self.initials}" if self.forenames else self.surname

    @property
    def name_sortable(self) -> str:
        if not self.forenames:
            return self.surname

        joiner = " " if self.surname_first else ", "
        return self.surname + joiner + (self.preferred_forenames or self.forenames)

    def get_absolute_url(self) -> str:
        return reverse("library:author_details", args=[str(self.slug)])

    def attribution_for(self, book: "Book", *_: Any, initials: bool = False) -> str:
        role = self.display_role_for_book(book)
        name = self.name_with_initials if initials else str(self)
        return name + (f" ({role})" if role else "")

    def is_editor_of(self, book: "Book") -> bool:
        return self.role_for_book(book) == "editor"

    def role_for_book(self, book: "Book") -> str:
        if book.first_author == self:
            return str(book.first_author_role)
        return rel.role if (rel := self.bookauthor_set.get(book=book.pk)) else ""

    def display_role_for_book(self, book: "Book") -> str:
        return "ed." if (role := self.role_for_book(book)) == "editor" else role

    @property
    def initials(self) -> str:
        if not self.forenames:
            return ""
        all_forenames = re.split(r"[. ]+", self.forenames)
        return ".".join([name[0] for name in all_forenames if name]) + "."

    @property
    def books(self) -> "BookQuerySet":
        return (
            self.first_authored_books.all() | self.additional_authored_books.all()
        ).distinct()

    @property
    def authored_books(self) -> "BookQuerySet":
        return (
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

    @property
    def edited_books(self) -> "BookQuerySet":
        return (
            self.books.filter(
                id__in=[ba.book.id for ba in self.bookauthor_set.filter(role="editor")]
            )
            | self.first_authored_books.filter(first_author_role="editor").distinct()
        )

    @property
    def identities(self) -> models.QuerySet["Author"]:
        identities = self.pseudonyms.all()
        if self.primary_identity:
            identities |= Author.objects.filter(id=self.primary_identity.id)
            identities |= self.primary_identity.identities

        if self in identities:
            identities &= Author.objects.exclude(id=self.id)
        return identities

    @staticmethod
    def normalise_name(name: str) -> dict[str, Any]:
        words = name.split(" ")
        surname = words.pop()
        while words and words[-1].lower() in [
            "von",
            "van",
            "der",
            "le",
            "de",
        ]:
            surname = f"{words.pop()} {surname}"

        forenames = " ".join(words)
        forenames = re.sub(r"\. +", ".", forenames)

        return {"surname": surname, "forenames": forenames}

    def _slug_fields(self) -> list[str]:
        return [
            remove_stopwords(self.name_with_initials, ["von", "van", "der", "le", "de"])
        ]
