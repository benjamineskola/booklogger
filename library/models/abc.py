from django.db import models
from django.utils import timezone


class SluggableModel(models.Model):
    class Meta:
        abstract = True

    slug = models.SlugField(blank=True, default="")


class TimestampedModel(models.Model):
    class Meta:
        abstract = True

    created_date = models.DateTimeField(db_index=True, default=timezone.now)
    modified_date = models.DateTimeField(db_index=True, default=timezone.now)
