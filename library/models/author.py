import re
from typing import Any, Dict, Iterable, MutableMapping, Optional, Tuple

import unidecode
from django.contrib.postgres.search import TrigramDistance
from django.db import models
from django.db.models import CheckConstraint, F, Q
from django.db.models.functions import Lower
from django.db.models.indexes import Index
from django.urls import reverse

from library.utils import LANGUAGES

Book = models.Model


class AuthorManager(models.Manager):  # type: ignore
    def search(self, pattern: str) -> "models.QuerySet[Author]":
        return Author.objects.annotate(
            sn_distance=TrigramDistance("surname", pattern),
            fn_distance=TrigramDistance("forenames", pattern),
            distance=F("sn_distance") * F("fn_distance"),
        ).order_by("distance")

    def get_by_single_name(self, name: str) -> "Author":
        return Author.objects.get(**Author.normalise_name(name))

    def get_or_create_by_single_name(self, name: str) -> Tuple["Author", bool]:
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

    def __str__(self) -> str:
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

    def get_link_data(
        self, book: Optional[Book] = None, **kwargs: Dict[str, Any]
    ) -> Dict[str, str]:
        return {
            "url": self.get_absolute_url(),
            "text": self.attribution_for(book, initials=False) if book else str(self),
        }

    def attribution_for(self, book: "Book", initials: bool = False) -> str:
        role = self._role_for_book(book)
        if initials:
            name = self.name_with_initials
        else:
            name = str(self)
        return name + (f" ({role})" if role else "")

    def _role_for_book(self, book: "Book") -> str:
        if book.first_author == self:  # type: ignore [attr-defined]
            if book.first_author_role == "editor":  # type: ignore [attr-defined]
                return "ed."
            else:
                return str(book.first_author_role)  # type: ignore [attr-defined]
        elif rel := self.bookauthor_set.get(book=book.id):  # type: ignore [attr-defined]
            return str(rel.display_role)
        else:
            return ""

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

        return {"surname": surname, "forenames": forenames}

    def _generate_slug(self) -> str:
        slug = "-".join(self.name_with_initials.lower().split(" "))
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
