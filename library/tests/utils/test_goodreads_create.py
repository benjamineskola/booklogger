from random import randrange

import pytest

from library.utils.goodreads_create import goodreads_create


@pytest.mark.django_db
class TestGoodreadsCreate:
    def test_create(self, faker):
        data = {
            "author": faker.name(),
            "title": faker.sentence(),
            "goodreads_id": str(randrange(1, 999999)),
            "first_published": str(randrange(1600, 2022)),
        }

        book = goodreads_create(data)

        assert book.title == data["title"]
        assert book.goodreads_id == data["goodreads_id"]
        assert book.first_published == data["first_published"]
        assert str(book.first_author) == data["author"]

    def test_create_with_series(self, faker):
        title = faker.sentence()
        series = faker.sentence()
        data = {
            "author": faker.name(),
            "title": f"{title} ({series}, #1)",
            "goodreads_id": str(randrange(1, 999999)),
            "first_published": str(randrange(1600, 2022)),
        }

        book = goodreads_create(data)

        assert book.title == title
        assert book.series == series
        assert book.series_order == 1
        assert book.goodreads_id == data["goodreads_id"]
        assert book.first_published == data["first_published"]
        assert str(book.first_author) == data["author"]

    def test_create_with_series_without_order(self, faker):
        title = faker.sentence()
        series = faker.sentence()
        data = {
            "author": faker.name(),
            "title": f"{title} ({series})",
            "goodreads_id": str(randrange(1, 999999)),
            "first_published": str(randrange(1600, 2022)),
        }

        book = goodreads_create(data)

        assert book.title == title
        assert book.series == series
        assert book.series_order is None
        assert book.goodreads_id == data["goodreads_id"]
        assert book.first_published == data["first_published"]
        assert str(book.first_author) == data["author"]

    def test_create_with_series_with_invalid_order(self, faker):
        title = faker.sentence()
        series = faker.sentence()
        data = {
            "author": faker.name(),
            "title": f"{title} ({series}, #what?)",
            "goodreads_id": str(randrange(1, 999999)),
            "first_published": str(randrange(1600, 2022)),
        }

        book = goodreads_create(data)

        assert book.title == title
        assert book.series == series
        assert book.series_order is None
        assert book.goodreads_id == data["goodreads_id"]
        assert book.first_published == data["first_published"]
        assert str(book.first_author) == data["author"]

    def test_create_with_isbn(self, faker):
        data = {
            "author": faker.name(),
            "title": faker.sentence(),
            "goodreads_id": str(randrange(1, 999999)),
            "first_published": str(randrange(1600, 2022)),
        }
        isbn = "978" + faker.password(
            special_chars=False, upper_case=False, lower_case=False
        )

        book = goodreads_create(data, isbn)

        assert book.isbn == isbn

    def test_create_with_asin(self, faker):
        data = {
            "author": faker.name(),
            "title": faker.sentence(),
            "goodreads_id": str(randrange(1, 999999)),
            "first_published": str(randrange(1600, 2022)),
        }
        asin = "B" + faker.password(9, special_chars=False, lower_case=False)

        book = goodreads_create(data, asin)

        assert book.isbn == ""
        assert book.asin == asin
