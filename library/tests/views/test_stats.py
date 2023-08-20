import pytest
from freezegun import freeze_time

from library.models.book import Tag
from library.views.stats import calculate_year_progress


@pytest.mark.django_db()
class TestStats:
    @pytest.fixture(autouse=True)
    def books(self, book_factory):
        books = [
            book_factory(page_count=50),
            book_factory(page_count=150),
            book_factory(page_count=75),
            book_factory(page_count=125),
        ]
        books[2].tags.add(Tag.objects.get(name="fiction"))
        books[3].tags.add(Tag.objects.get(name="non-fiction"))

        for book in books:
            book.start_reading()
            book.finish_reading()
        return books

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
