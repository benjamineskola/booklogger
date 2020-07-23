import re
from typing import Any, MutableMapping, Tuple, Set

import unidecode
from django.contrib.postgres.search import TrigramSimilarity
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.db.models.indexes import Index
from django.urls import reverse

from library.utils import LANGUAGES

Book = models.Model


class AuthorManager(models.Manager):  # type: ignore
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

    def get_or_create_by_single_name(self, name: str) -> Tuple["Author", bool]:
        try:
            return (Author.objects.get_by_single_name(name), False)
        except self.model.DoesNotExist:
            return Author.objects.get_or_create(**Author.normalise_name(name))

    def regenerate_all_slugs(self) -> None:
        qs = self.get_queryset()
        qs.update(slug="")
        for author in qs:
            author.slug = author._generate_slug()
            author.save()


class Author(models.Model):
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
        elif self.surname_first:
            return self.surname + " " + (self.preferred_forenames or self.forenames)
        else:
            return (self.preferred_forenames or self.forenames) + " " + self.surname

    @property
    def full_name(self) -> str:
        if not self.forenames:
            return self.surname
        elif self.surname_first:
            return self.surname + " " + self.forenames
        else:
            return self.forenames + " " + self.surname

    @property
    def name_with_initials(self) -> str:
        if self.forenames:
            return self.surname + ", " + self.initials
        else:
            return self.surname

    def get_absolute_url(self) -> str:
        return reverse("library:author_details", args=[str(self.slug)])

    def attribution_for(self, book: "Book", initials: bool = False) -> str:
        role = self.display_role_for_book(book)
        if initials:
            name = self.name_with_initials
        else:
            name = str(self)
        return name + (f" ({role})" if role else "")

    def is_editor_of(self, book: "Book") -> bool:
        return self.role_for_book(book) == "editor"

    def role_for_book(self, book: "Book") -> str:
        if book.first_author == self:  # type: ignore [attr-defined]
            return str(book.first_author_role)  # type: ignore [attr-defined]
        elif rel := self.bookauthor_set.get(book=book.pk):
            return rel.role
        else:
            return ""

    def display_role_for_book(self, book: "Book") -> str:
        return "ed." if (role := self.role_for_book(book)) == "editor" else role

    @property
    def initials(self) -> str:
        if not self.forenames:
            return ""
        all_forenames = re.split(r"[. ]+", self.forenames)
        return ".".join([name[0] for name in all_forenames if name]) + "."

    @property
    def books(self) -> "models.QuerySet[Book]":
        return (
            self.first_authored_books.all() | self.additional_authored_books.all()
        ).distinct()

    @property
    def authored_books(self) -> "models.QuerySet[Book]":
        books: "models.QuerySet[Book]" = (
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
    def edited_books(self) -> "models.QuerySet[Book]":
        books: "models.QuerySet[Book]" = (
            self.books.filter(
                id__in=[ba.book.id for ba in self.bookauthor_set.filter(role="editor")]
            )
            | self.first_authored_books.filter(first_author_role="editor").distinct()
        )
        return books

    @property
    def identities(self) -> Set["Author"]:
        identities = set(self.pseudonyms.all())
        if self.primary_identity:
            identities.add(self.primary_identity)
            identities |= self.primary_identity.identities

        if self in identities:
            identities.remove(self)
        return identities

    @staticmethod
    def normalise_name(name: str) -> MutableMapping[str, str]:
        words = name.split(" ")
        surname = words.pop()
        while words and words[-1].lower() in [
            "von",
            "van",
            "der",
            "le",
            "de",
        ]:
            surname = words.pop() + " " + surname

        forenames = " ".join(words)
        forenames = re.sub(r"\. +", ".", forenames)

        return {"surname": surname, "forenames": forenames}

    def _generate_slug(self) -> str:
        words = self.name_with_initials.lower().split(" ")
        slug = "-".join(
            [word for word in words if word not in ["von", "van", "der", "le", "de"]]
        )
        slug = unidecode.unidecode(slug)
        slug = re.sub(r"[^\w-]+", "", slug)

        slug = slug[0:50].strip("-")
        matches = Author.objects.filter(slug__regex=f"^{slug}(-\\d+)?$")
        if matches:
            slug = slug[0:48].strip("-") + "-" + str(matches.count())

        return slug

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = self._generate_slug()

        super().save(*args, **kwargs)
