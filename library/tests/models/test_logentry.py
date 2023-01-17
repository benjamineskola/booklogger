import pytest
from django.utils import timezone

from library.models import LogEntry


@pytest.mark.django_db()
class TestLogEntry:
    def test_no_log_entries(self, book):
        assert book.log_entries.count() == 0

    def test_currently_reading(self, book):
        today = timezone.now().date()
        book.start_reading()
        assert book.log_entries.count() == 1
        assert book.log_entries.all()[0].start_date.date() == today
        assert not book.log_entries.all()[0].end_date

    def test_currently_reading_method(self, book):
        assert not book.currently_reading
        book.start_reading()
        assert book.currently_reading
        book.finish_reading()
        assert not book.currently_reading

    def test_stop_reading(self, book):
        today = timezone.now().date()
        book.start_reading()
        book.finish_reading()
        assert book.log_entries.count() == 1
        assert book.log_entries.all()[0].start_date.date() == today
        assert book.log_entries.all()[0].end_date.date() == today

    def test_cannot_start_twice(self, book):
        book.start_reading()
        book.start_reading()
        assert book.log_entries.count() == 1

    def test_cannot_finish_before_starting(self, book):
        with pytest.raises(LogEntry.DoesNotExist):
            book.finish_reading()
