from datetime import timedelta

import pytest
from django.utils import timezone

from library.factories import book_factory  # noqa: F401


@pytest.mark.django_db
class TestTimestampedModel:
    def test_created_date(self, book_factory):  # noqa: F811
        test_start = timezone.now()
        book = book_factory()
        book.save()
        test_end = timezone.now()

        assert book.created_date > test_start
        assert book.created_date < test_end
        assert abs(book.modified_date - book.created_date) < timedelta(seconds=1)

    def test_modified_date(self, book_factory):  # noqa: F811
        book = book_factory()
        book.save()
        orig_modified_date = book.modified_date

        test_start = timezone.now()
        book.title = "dummy title"
        book.save()
        test_end = timezone.now()

        assert book.modified_date != orig_modified_date
        assert book.created_date < test_start
        assert book.modified_date > test_start
        assert book.modified_date < test_end
