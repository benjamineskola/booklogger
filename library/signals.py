from typing import Any

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from library.models import LogEntry, StatisticsReport
from library.models.abc import TimestampedModel


@receiver(pre_save)
def update_timestamp_on_save(
    sender: type[TimestampedModel],
    instance: TimestampedModel,
    raw: bool,  # pylint:disable=unused-argument
    using: str,  # pylint:disable=unused-argument
    update_fields: dict[str, Any],  # pylint:disable=unused-argument
    **_kwargs: Any
) -> None:
    if issubclass(sender, TimestampedModel):
        instance.modified_date = timezone.now()


@receiver(post_save)
def update_report_on_save(  # pylint:disable=too-many-arguments
    sender: type[LogEntry],  # pylint:disable=unused-argument
    instance: LogEntry,
    created: bool,  # pylint:disable=unused-argument
    raw: bool,  # pylint:disable=unused-argument
    using: str,  # pylint:disable=unused-argument
    update_fields: dict[str, Any],  # pylint:disable=unused-argument
    **_kwargs: Any
) -> None:
    if isinstance(sender, LogEntry) and instance.end_date:
        report, report_created = StatisticsReport.get_or_create(
            year=instance.end_date.year
        )
        if not report_created:
            report.generate()
            report.save()
