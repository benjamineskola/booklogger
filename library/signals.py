from typing import Any, Type

from django.utils import timezone

from library.models.timestamped_model import TimestampedModel


def update_timestamp_on_save(
    sender: Type[TimestampedModel],
    instance: TimestampedModel,
    raw: bool,
    using: str,
    update_fields: dict[str, Any],
    **kwargs: Any
) -> None:
    instance.modified_date = timezone.now()
