import pytest

from library.models import Book, Tag
from library.views.stats import _stats_for_queryset


@pytest.mark.django_db
class TestStats:
    @pytest.fixture
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

    def test_stats_for_queryset_counts(self, stats, books):
        assert stats["count"] == 4
        assert stats["pages"] == 400
        assert stats["average_pages"] == 100
        assert stats["shortest_book"] == books[0]
        assert stats["longest_book"] == books[1]

    def test_stats_for_queryset_genre(self, stats, books):
        assert stats["fiction"]["count"] == 1
        assert stats["non-fiction"]["count"] == 1

        assert stats["fiction"]["pages"] == 75
        assert stats["non-fiction"]["pages"] == 125
