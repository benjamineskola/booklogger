import pytest
from django.utils import timezone

from library.factories import book_factory  # noqa: F401
from library.models import LogEntry


@pytest.mark.django_db
class TestLogEntry:
    @pytest.fixture
    def mock_book(self, book_factory):  # noqa: F811
        mock_book = book_factory(title="The Bible")
        mock_book.save()
        return mock_book

    def test_no_log_entries(self, mock_book):
        assert mock_book.log_entries.count() == 0

    def test_currently_reading(self, mock_book):
        today = timezone.now().date()
        mock_book.start_reading()
        assert mock_book.log_entries.count() == 1
        assert mock_book.log_entries.all()[0].start_date.date() == today
        assert not mock_book.log_entries.all()[0].end_date

    def test_currently_reading_method(self, mock_book):
        assert not mock_book.currently_reading
        mock_book.start_reading()
        assert mock_book.currently_reading
        mock_book.finish_reading()
        assert not mock_book.currently_reading

    def test_stop_reading(self, mock_book):
        today = timezone.now().date()
        mock_book.start_reading()
        mock_book.finish_reading()
        assert mock_book.log_entries.count() == 1
        assert mock_book.log_entries.all()[0].start_date.date() == today
        assert mock_book.log_entries.all()[0].end_date.date() == today

    def test_cannot_start_twice(self, mock_book):
        mock_book.start_reading()
        mock_book.start_reading()
        assert mock_book.log_entries.count() == 1

    def test_cannot_finish_before_starting(self, mock_book):
        with pytest.raises(LogEntry.DoesNotExist):
            mock_book.finish_reading()
