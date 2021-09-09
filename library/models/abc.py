import re
from typing import Any

from django.db import models
from django.utils import timezone
from stripunicode import stripunicode


class SluggableModel(models.Model):
    class Meta:
        abstract = True

    slug = models.SlugField(blank=True, default="")
    id: Any

    def _slug_fields(self) -> list[str]:
        raise NotImplementedError

    def _generate_slug(self) -> str:
        slug = "-".join(
            [field.lower().replace(" ", "-") for field in self._slug_fields()]
        )
        slug = stripunicode(slug)
        slug = re.sub(r"[^\w-]+", "", slug)

        slug = slug[0:50].strip("-")
        matches = self.__class__.objects.filter(slug=slug).exclude(pk=self.id)
        if not matches:
            return slug
        elif matches.count() == 1 and matches.first() == self:
            return slug
        else:
            for idx in range(1, 10):
                new_slug = slug[0:48].strip("-") + "-" + str(idx)
                matches = self.__class__.objects.filter(slug=new_slug).exclude(
                    pk=self.id
                )
                if not matches:
                    return new_slug
        return str(self.id)

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = self._generate_slug()

        super().save(*args, **kwargs)


class TimestampedModel(models.Model):
    class Meta:
        abstract = True

    created_date = models.DateTimeField(db_index=True, default=timezone.now)
    modified_date = models.DateTimeField(db_index=True, default=timezone.now)
