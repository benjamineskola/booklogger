from pathlib import Path

import pytest

from library.utils import verso


@pytest.mark.django_db()
class TestVerso:
    def test_not_verso(self, book_factory):
        book = book_factory(publisher="Penguin")
        verso.update(book)

        assert not book.publisher_url
        assert not book.image_url

    def test_already_set(self, book_factory):
        dummy_url = "http://somewhere.invalid/://versobooks.com"
        book = book_factory(
            publisher="Verso", image_url=dummy_url, publisher_url=dummy_url
        )

        verso.update(book)

        assert book.publisher_url == dummy_url
        assert book.image_url == dummy_url

    def test_update_from_publisher_url(self, book_factory, requests_mock):
        with Path("library/fixtures/losurdo.html").open() as file:
            requests_mock.get(
                "https://www.versobooks.com/books/960-liberalism",
                text=file.read(),
            )

        book = book_factory(
            publisher="Verso",
            publisher_url="https://www.versobooks.com/books/960-liberalism",
        )

        assert book.image_url
