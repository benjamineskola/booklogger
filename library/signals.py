from typing import Any, Type

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from library.models.timestamped_model import TimestampedModel


@receiver(pre_save)
def update_timestamp_on_save(
    sender: Type[TimestampedModel],
    instance: TimestampedModel,
    raw: bool,
    using: str,
    update_fields: dict[str, Any],
    **kwargs: Any
) -> None:
    if issubclass(sender, TimestampedModel):
        instance.modified_date = timezone.now()
