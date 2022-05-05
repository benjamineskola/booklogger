from typing import Any

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

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
