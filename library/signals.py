from typing import Any

from django.db.models import Model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from library.models import Author, Book, LogEntry, StatisticsReport
from library.models.abc import TimestampedModel


@receiver(pre_save)
def update_timestamp_on_save(
    sender: type[TimestampedModel],
    instance: TimestampedModel,
    raw: bool,  # noqa: ARG001, FBT001
    using: str,  # noqa: ARG001
    update_fields: dict[str, Any],  # noqa: ARG001
    **_kwargs: Any
) -> None:
    if issubclass(sender, TimestampedModel):
        instance.modified_date = timezone.now()


@receiver(post_save)
def update_report_on_save(
    sender: type[Model],  # noqa: ARG001
    instance: Model,
    created: bool,  # noqa: ARG001, FBT001
    raw: bool,  # noqa: ARG001, FBT001
    using: str,  # noqa: ARG001
    update_fields: dict[str, Any],  # noqa: ARG001
    **_kwargs: Any
) -> None:

    years = []
    if isinstance(instance, LogEntry) and instance.end_date:
        years = [instance.end_date.year]
    elif isinstance(instance, Author):
        years = list(
            instance.books.read().values_list("log_entries__end_date__year", flat=True)
        )
    elif isinstance(instance, Book):
        years = list(
            instance.log_entries.exclude(end_date__isnull=True).values_list(
                "end_date__year", flat=True
            )
        )

    if not years:
        return

    for year in years + [1, 0]:
        report, report_created = StatisticsReport.objects.get_or_create(year=year)
        if not report_created:
            report.generate()
            report.save()
