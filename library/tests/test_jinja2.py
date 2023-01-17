from datetime import datetime

import pytest
from django.utils import timezone

from booklogger import jinja2


@pytest.mark.django_db()
class TestJinja:
    @pytest.fixture()
    def books(self, book_factory, user):
        tz = timezone.get_default_timezone()
        return [
            book_factory(acquired_date=datetime(1970, 1, 1, tzinfo=tz), owned_by=user),
            book_factory(acquired_date=datetime(2000, 1, 1, tzinfo=tz), owned_by=user),
            book_factory(acquired_date=datetime(1970, 1, 1, tzinfo=tz), owned_by=user),
            book_factory(acquired_date=datetime(1, 1, 1, tzinfo=tz), owned_by=user),
            book_factory(),
        ]

    def test_groupby_date(self, books):
        result = jinja2.groupby_date(books, "acquired_date")

        assert result[0][0] == "None"
        assert result[1][0] == "01 January, 1970"
        assert result[2][0] == "01 January, 2000"
        assert result[3][0] == "None"

        assert result[1][1] == [books[0], books[2]]
        assert result[2][1] == [books[1]]
        assert result[3][1] == [books[4]]

    def test_groupby_date_not_a_date(self, books):
        result = jinja2.groupby_date(books, "title")

        keys = [i[0] for i in result]
        assert sorted(keys) == sorted(book.title for book in books)
