from typing import Any

from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from .author import Author
from .book import Book

from library.utils import str2bool


class LogEntryManager(models.Manager):  # type: ignore [type-arg]
    def get_queryset(self) -> "LogEntryQuerySet":
        return LogEntryQuerySet(self.model, using=self._db)

    def filter_by_request(self, request: Any) -> "LogEntryQuerySet":
        return self.get_queryset().filter_by_request(request)


class LogEntryQuerySet(models.QuerySet):  # type: ignore [type-arg]
    def filter_by_request(self, request: Any) -> "LogEntryQuerySet":
        filter_by = Q()
        if gender := request.GET.get("gender"):
            if gender.lower() == "multiple":
                filter_by &= Q(book__additional_authors__isnull=False)
                filter_by &= Q(
                    book__additional_authors__gender__lt=F("book__first_author__gender")
                ) | Q(book__additional_authors__gender__gt=F("book__first_author__gender"))
            elif gender.lower() == "nonmale":
                filter_by &= Q(book__first_author__gender__in=[0, 2, 4]) | Q(
                    book__additional_authors__gender__in=[0, 2, 4]
                )
            else:
                if not gender.isdigit():
                    gender = Author.Gender[gender.upper()]
                filter_by &= Q(book__first_author__gender=gender) | Q(
                    book__additional_authors__gender=gender
                )
        if poc := request.GET.get("poc"):
            val = str2bool(poc)
            filter_by &= Q(book__first_author__poc=val) | Q(
                book__additional_authors__poc=val
            )
        if tags := request.GET.get("tags"):
            filter_by &= Q(
                book__tags__contains=[tag.strip().lower() for tag in tags.split(",")]
            )
        if owned := request.GET.get("owned"):
            try:
                val = not str2bool(owned)
                filter_by &= Q(book__owned_by__isnull=val)
            except ValueError:
                filter_by &= Q(book__owned_by__username=owned)

        return self.filter(filter_by)


class LogEntry(models.Model):
    objects = LogEntryManager()

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="log_entries")
    start_date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    end_date = models.DateTimeField(db_index=True, blank=True, null=True)
    progress_percentage = models.FloatField(default=0)
    progress_page = models.PositiveSmallIntegerField(default=0)
    progress_date = models.DateTimeField(db_index=True, default=timezone.now)

    class DatePrecision(models.IntegerChoices):
        DAY = 0
        MONTH = 1
        YEAR = 2

    start_precision = models.PositiveSmallIntegerField(
        choices=DatePrecision.choices, default=0
    )
    end_precision = models.PositiveSmallIntegerField(
        choices=DatePrecision.choices, default=0
    )

    def __str__(self) -> str:
        text = str(self.book)
        if self.start_date:
            text += f" from {self.start_date.strftime('%Y-%m-%d')}"
        if self.end_date:
            text += f" to {self.end_date.strftime('%Y-%m-%d')}"
        else:
            text += ", unfinished"
        return text

    @property
    def currently_reading(self) -> bool:
        if self.start_date and not self.end_date:
            return True
        else:
            return False
