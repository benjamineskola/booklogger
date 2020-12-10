from django.db import models
from django.db.models import signals
from django.urls import reverse
from django.utils import timezone

from library.models.book import Book
from library.signals import update_timestamp_on_save


class ReadingList(models.Model):
    title = models.CharField(db_index=True, max_length=255)
    books = models.ManyToManyField(
        Book,
        through="ReadingListEntry",
        related_name="reading_lists",
        blank=True,
    )

    created_date = models.DateTimeField(db_index=True, default=timezone.now)
    modified_date = models.DateTimeField(db_index=True, default=timezone.now)

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("library:list_details", kwargs={"pk": self.id})


class ReadingListEntry(models.Model):
    class Meta:
        ordering = ["order"]
        unique_together = ("reading_list", "book")

    reading_list = models.ForeignKey(ReadingList, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(db_index=True, blank=True, null=True)
    created_date = models.DateTimeField(db_index=True, default=timezone.now)
    modified_date = models.DateTimeField(db_index=True, default=timezone.now)


signals.pre_save.connect(receiver=update_timestamp_on_save, sender=ReadingList)
signals.pre_save.connect(receiver=update_timestamp_on_save, sender=ReadingListEntry)
