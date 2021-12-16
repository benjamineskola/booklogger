from django.db import models
from django.urls import reverse

from library.models.book import Book
from library.models.abc import TimestampedModel


class ReadingList(TimestampedModel):
    title = models.CharField(db_index=True, max_length=255)
    books = models.ManyToManyField(
        Book,
        through="ReadingListEntry",
        related_name="reading_lists",
        blank=True,
    )

    def __str__(self) -> str:  # pylint:disable=invalid-str-returned
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("library:list_details", kwargs={"pk": self.id})


class ReadingListEntry(TimestampedModel):
    class Meta:
        ordering = ["order"]
        unique_together = ("reading_list", "book")

    reading_list = models.ForeignKey(ReadingList, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(db_index=True, blank=True, null=True)
