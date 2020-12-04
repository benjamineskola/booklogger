from django.utils import timezone


def update_timestamp_on_save(sender, instance, raw, using, update_fields, **kwargs):  # type: ignore [no-untyped-def]
    instance.modified_date = timezone.now()
