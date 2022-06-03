from typing import Any

from django.db import models

from library.models.abc import TimestampedModel
from library.models.author import Author
from library.models.book import Book, BookQuerySet
from library.models.log_entry import LogEntry

GENRES = ["fiction", "non-fiction"]

Numeric = int | float


class StatisticsReport(TimestampedModel):
    year = models.PositiveSmallIntegerField(primary_key=True)
    count = models.PositiveSmallIntegerField()
    page_count = models.PositiveIntegerField()
    average_pages = models.FloatField()
    longest = models.ForeignKey(
        Book, null=True, related_name="longest_in_year", on_delete=models.SET_NULL
    )
    shortest = models.ForeignKey(
        Book, null=True, related_name="shortest_in_year", on_delete=models.SET_NULL
    )

    by_men = models.JSONField()
    by_women = models.JSONField()
    by_multiple = models.JSONField()
    by_organisations = models.JSONField()
    by_nonbinary = models.JSONField()
    by_poc = models.JSONField()

    fiction = models.JSONField()
    nonfiction = models.JSONField()

    gender_breakdowns = models.JSONField()
    genre_breakdowns = models.JSONField()

    # derived properties

    # methods

    def generate(self) -> None:
        if self.year:
            logs = LogEntry.objects.filter(end_date__year=self.year)
        else:
            logs = LogEntry.objects.filter(end_date__isnull=False)
        books = Book.objects.filter(id__in=logs.values_list("book_id", flat=True))

        self.count = books.count()
        self.page_count = books.page_count
        self.average_pages = self.page_count / max(
            1, books.exclude(page_count=0).count()
        )

        if self.count:
            self.shortest = books.order_by("page_count")[0]
            self.longest = books.order_by("-page_count")[0]

        self.by_men = self._counts_for_queryset(
            books.by_men(), self.count, self.page_count
        )
        self.by_women = self._counts_for_queryset(
            books.by_women(), self.count, self.page_count
        )
        self.by_multiple = self._counts_for_queryset(
            books.by_multiple_genders(), self.count, self.page_count
        )
        self.by_organisations = self._counts_for_queryset(
            books.by_gender(3), self.count, self.page_count
        )
        self.by_nonbinary = self._counts_for_queryset(
            books.by_gender(4), self.count, self.page_count
        )
        self.by_poc = self._counts_for_queryset(
            books.poc(), self.count, self.page_count
        )

        self.fiction = self._counts_for_queryset(
            books.fiction(), self.count, self.page_count
        )
        self.nonfiction = self._counts_for_queryset(
            books.nonfiction(), self.count, self.page_count
        )

        self.gender_breakdowns = {
            int(i): {
                genre: self._counts_for_queryset(
                    books.tagged(genre).by_gender(i),
                    books.by_gender(i).count(),
                    books.by_gender(i).page_count,
                )
                for genre in GENRES
            }
            for i in Author.Gender
        }
        self.genre_breakdowns = {
            genre: {
                int(i): self._counts_for_queryset(
                    books.tagged(genre).by_gender(i),
                    books.tagged(genre).count(),
                    books.tagged(genre).page_count,
                )
                for i in Author.Gender
            }
            for genre in ["fiction", "non-fiction"]
        }

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.count is None:
            self.generate()

        super().save(*args, **kwargs)

    def _counts_for_queryset(
        self, qs: BookQuerySet, total_count: int, total_pages: int
    ) -> dict[str, Numeric]:
        return {
            "count": qs.count(),
            "page_count": qs.page_count,
            "percent": qs.count() / max(1, total_count) * 100,
            "pages_percent": qs.page_count / max(1, total_pages) * 100,
        }
