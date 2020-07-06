from datetime import datetime
from typing import Any, Optional

from django.db import models
from django.db.models import Q
from django.utils import timezone

from .author import Author
from .book import Book


class LogEntryManager(models.Manager):  # type: ignore [type-arg]
    def get_queryset(self) -> "LogEntryQuerySet":
        return LogEntryQuerySet(self.model, using=self._db)

    def filter_by_request(self, request: Any) -> "LogEntryQuerySet":
        return self.get_queryset().filter_by_request(request)


class LogEntryQuerySet(models.QuerySet):  # type: ignore [type-arg]
    def filter_by_request(self, request: Any) -> "LogEntryQuerySet":
        filter_by = Q()
        if gender := request.GET.get("gender"):
            if not gender.isdigit():
                gender = Author.Gender[gender.upper()]
            filter_by &= Q(book__first_author__gender=gender) | Q(
                book__additional_authors__gender=gender
            )
        if poc := request.GET.get("poc"):
            filter_by &= Q(book__first_author__poc=bool(int(poc))) | Q(
                book__additional_authors__poc=bool(int(poc))
            )
        if tags := request.GET.get("tags"):
            filter_by &= Q(
                book__tags__contains=[tag.strip().lower() for tag in tags.split(",")]
            )
        if owned := request.GET.get("owned"):
            if owned == "true":
                filter_by &= Q(book__owned_by__isnull=False)
            elif owned == "false":
                filter_by &= Q(book__owned_by__isnull=True)
            else:
                filter_by &= Q(book__owned_by__id=owned)

        return self.filter(filter_by)


class LogEntry(models.Model):
    objects = LogEntryManager()

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="log_entries")
    start_date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    end_date = models.DateTimeField(db_index=True, blank=True, null=True)
    progress = models.PositiveSmallIntegerField(default=0)
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
            text += f" from {self.start_date_display}"
        if self.end_date:
            text += f" to {self.end_date_display}"
        else:
            text += ", unfinished"
        return text

    @property
    def currently_reading(self) -> bool:
        if self.start_date and not self.end_date:
            return True
        else:
            return False

    @property
    def start_date_display(self) -> str:
        return self._date_with_precision(self.start_date, self.start_precision)

    @property
    def end_date_display(self) -> str:
        return self._date_with_precision(self.end_date, self.end_precision)

    @property
    def progress_date_display(self) -> str:
        return self._date_with_precision(self.progress_date, 0)

    def _date_with_precision(self, date: Optional[datetime], precision: int) -> str:
        if not date:
            return ""

        if precision == 2:
            return date.strftime("%Y")
        elif precision == 1:
            return date.strftime("%B %Y")
        elif (timezone.now() - date).days < 270:
            return date.strftime("%d %B")
        else:
            return date.strftime("%d %B, %Y")
