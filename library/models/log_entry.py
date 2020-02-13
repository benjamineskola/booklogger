from django.db import models
from django.utils import timezone

from .book import Book


class LogEntryManager(models.Manager):
    def get_queryset(self):
        return LogEntryQuerySet(self.model, using=self._db)

    def filter_by_request(self, request):
        return self.get_queryset().filter_by_request(request)


class LogEntryQuerySet(models.QuerySet):
    def filter_by_request(self, request):
        filter_by = {}
        if gender := request.GET.get("gender"):
            filter_by["book__first_author__gender"] = gender
        if poc := request.GET.get("poc"):
            filter_by["book__first_author__poc"] = bool(int(poc))
        if tags := request.GET.get("tags"):
            filter_by["book__tag__contains"] = [tag.strip() for tag in tags.split(",")]

        return self.filter(**filter_by)


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

    def __str__(self):
        return f"{self.book} from {self.start_date} to {self.end_date}"

    @property
    def currently_reading(self):
        if self.start_date and not self.end_date:
            return True
        else:
            return False

    @property
    def start_date_display(self):
        return self._date_with_precision(self.start_date, self.start_precision)

    @property
    def end_date_display(self):
        return self._date_with_precision(self.end_date, self.end_precision)

    @property
    def progress_date_display(self):
        return self._date_with_precision(self.progress_date, 0)

    def _date_with_precision(self, date, precision):
        if not date:
            return

        if precision == 2:
            return date.strftime("%Y")
        elif precision == 1:
            return date.strftime("%B %Y")
        elif (timezone.now() - date).days < 270:
            return date.strftime("%d %B")
        else:
            return date.strftime("%d %B, %Y")
