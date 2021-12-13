from typing import Any

from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from library.models.abc import TimestampedModel
from library.utils import str2bool

from .author import Author
from .book import Book


class LogEntryQuerySet(models.QuerySet["LogEntry"]):
    def by_gender(self, *genders: int) -> "LogEntryQuerySet":
        return self.filter(
            Q(book__first_author__gender__in=genders)
            | Q(book__additional_authors__gender__in=genders)
        )

    def filter_by_request(self, request: Any) -> "LogEntryQuerySet":
        qs = self
        if gender := request.GET.get("gender"):
            if gender.lower() == "multiple":
                qs = qs.filter(book__additional_authors__isnull=False).filter(
                    book__additional_authors__gender__ne=F("book__first_author__gender")
                )

            elif gender.lower() == "nonmale":
                qs = qs.by_gender(0, 2, 4)
            else:
                if not gender.isdigit():
                    gender = Author.Gender[gender.upper()]
                qs = qs.by_gender(gender)
        if poc := request.GET.get("poc"):
            val = str2bool(poc)
            qs = qs.filter(
                Q(book__first_author__poc=val) | Q(book__additional_authors__poc=val)
            )
        if tags := request.GET.get("tags"):
            qs = qs.filter(
                book__tags__contains=[tag.strip() for tag in tags.lower().split(",")]
            )
        if owned := request.GET.get("owned"):
            try:
                val = not str2bool(owned)
                qs = qs.filter(book__owned_by__isnull=val)
            except ValueError:
                qs = qs.filter(book__owned_by__username=owned)
        if want_to_read := request.GET.get("want_to_read"):
            qs = qs.filter(book__want_to_read=str2bool(want_to_read))

        return qs


LogEntryManager = models.Manager.from_queryset(LogEntryQuerySet)


class LogEntry(TimestampedModel):
    objects = LogEntryManager()

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="log_entries")
    start_date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    end_date = models.DateTimeField(db_index=True, blank=True, null=True)
    progress_percentage = models.FloatField(default=0)
    progress_page = models.PositiveSmallIntegerField(default=0)
    progress_date = models.DateTimeField(db_index=True, default=timezone.now)

    exclude_from_stats = models.BooleanField(default=False)

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
        return self.start_date is not None and self.end_date is None
