import operator
from functools import reduce
from typing import TYPE_CHECKING, Any

from django.db import models
from django.urls import reverse

from library.models.abc import TimestampedModel

if TYPE_CHECKING:
    from .book import BookQuerySet  # pragma: no cover


class TagManager(models.Manager["Tag"]):
    def get(self, name: str) -> "Tag":
        tag, _ = Tag.objects.get_or_create(name=name.lower().strip())
        return tag


class Tag(TimestampedModel):
    objects = TagManager()

    class Meta:
        ordering = ("name",)

    name = models.CharField(max_length=64, primary_key=True)
    parents = models.ManyToManyField(
        "self", related_name="children", blank=True, symmetrical=False
    )

    def __str__(self) -> str:
        return self.fullname

    @property
    def fullname(self) -> str:
        if parent := self.parents.first():
            return parent.fullname + " :: " + self.name
        return self.name

    @property
    def books_recursive(self) -> "BookQuerySet":
        books = self.books.distinct()
        for child in self.children.all():
            books |= child.books_recursive.distinct()
        return books

    @property
    def books_uniquely_tagged(self) -> "BookQuerySet":
        others = Tag.objects.exclude(name__in=[self.name, "fiction", "non-fiction"])
        return self.books_recursive.exclude(tags__in=others)

    @property
    def parents_recursive(self) -> models.QuerySet["Tag"]:
        return reduce(
            operator.or_,
            [p.parents_recursive for p in self.parents.all()],
            self.parents.all(),
        )

    @property
    def children_recursive(self) -> models.QuerySet["Tag"]:
        return reduce(
            operator.or_,
            [c.children_recursive for c in self.children.all()],
            self.children.all(),
        )

    @property
    def related(self) -> models.QuerySet["Tag"]:
        return reduce(
            operator.or_,
            [
                Tag.objects.filter(
                    name__in=[tag.name for tag in book.tags.all() if tag != self]
                )
                for book in self.books.all()
            ],
            Tag.objects.none(),
        )

    def __lt__(self, other: "Tag") -> bool:
        return self.name < other.name

    def get_absolute_url(self) -> str:
        return reverse("library:tag_details", args=[self.name])

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.name = self.name.lower()
        super().save(*args, **kwargs)
