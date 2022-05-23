import pytest
from freezegun import freeze_time

from library.models import Book, Tag
from library.views.stats import (
    _counts_for_queryset,
    _stats_for_queryset,
    calculate_year_progress,
)


@pytest.mark.django_db
class TestStats:
    @pytest.fixture(autouse=True)
    def books(self, book_factory):
        Tag(name="fiction").save()
        Tag(name="non-fiction").save()

        books = [
            book_factory(page_count=50),
            book_factory(page_count=150),
            book_factory(page_count=75, tags=["fiction"]),
            book_factory(page_count=125, tags=["non-fiction"]),
        ]

        for book in books:
            book.start_reading()
            book.finish_reading()
        yield books

    @pytest.fixture
    def stats(self, books):
        yield _stats_for_queryset(Book.objects.all())

    def test_counts_for_queryset(self):
        counts = _counts_for_queryset(Book.objects.all())
        assert counts["count"] == 4
        assert counts["pages"] == 400

    def test_counts_for_queryset_percentages(self):
        all_books = Book.objects.all()
        counts = _counts_for_queryset(
            all_books.tagged("fiction"), all_books.count(), all_books.page_count
        )

        assert counts["percent"] == 0.25
        assert counts["pages_percent"] == 0.1875

    def test_stats_for_queryset_counts(self, stats, books):
        assert stats["average_pages"] == 100
        assert stats["shortest_book"] == books[0]
        assert stats["longest_book"] == books[1]

    def test_stats_for_queryset_genre(self, stats, books):
        assert stats["fiction"]["count"] == 1
        assert stats["non-fiction"]["count"] == 1

        assert stats["fiction"]["pages"] == 75
        assert stats["non-fiction"]["pages"] == 125

    @freeze_time("2022-01-01")
    def test_calculate_year_progress_nyd(self):
        assert calculate_year_progress(2022) == (1, 365)

    @freeze_time("2022-12-31")
    def test_calculate_year_progress_nye(self):
        assert calculate_year_progress(2022) == (365, 365)

    @freeze_time("2022-06-30")
    def test_calculate_year_progress_midsummer(self):
        assert calculate_year_progress(2022) == (181, 365)

    @freeze_time("2024-02-29")
    def test_calculate_year_progress_leap(self):
        assert calculate_year_progress(2024) == (60, 366)

    @freeze_time("2024-12-31")
    def test_calculate_year_progress_leap_nye(self):
        assert calculate_year_progress(2024) == (366, 366)
