from typing import Any

from django.db import models


class BookWithEditions(models.Model):
    editions = models.ManyToManyField("self", symmetrical=True, blank=True)

    class Meta:
        abstract = True

    @property
    def _fields_to_copy(self) -> dict[str, Any]:
        field_names = [
            "title",
            "subtitle",
            "first_author",
            "first_author_role",
            "first_published",
            "language",
            "want_to_read",
            "tags_list",
            "review",
            "rating",
            "series",
            "series_order",
            "private",
        ]

        return {name: getattr(self, name) for name in field_names}

    def get_edition_disambiguator(self) -> str:
        edition_language = getattr(self, "edition_language", "")
        if self.editions.exclude(edition_language=edition_language).count():  # type: ignore[misc]
            if edition_language:
                return self.get_edition_language_display()  # type: ignore[attr-defined,no-any-return]
            return self.get_language_display()  # type: ignore[attr-defined,no-any-return]
        return self.get_edition_format_display().lower()  # type: ignore[attr-defined,no-any-return]

    def create_new_edition(self, edition_format: int) -> "BookWithEditions":
        edition = self.__class__(
            **self._fields_to_copy,
            edition_format=edition_format,  # type: ignore[misc]
            # technically this is per-edition but this is convenient
            goodreads_id=getattr(self, "goodreads_id", "")
        )
        edition.save()
        for author in self.bookauthor_set.all():  # type: ignore[attr-defined]
            edition.add_author(author.author, role=author.role, order=author.order)  # type: ignore[attr-defined]
        self.editions.add(edition)
        self.save()
        return edition

    def save_other_editions(self) -> None:
        self.editions.all().update(**self._fields_to_copy)
