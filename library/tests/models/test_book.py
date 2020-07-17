import pytest

from library.factories import (  # noqa: F401
    author_factory,
    book_author_factory,
    book_factory,
)


@pytest.mark.django_db
class TestBook:
    @pytest.fixture
    def mock_authors(self, author_factory):  # noqa: F811
        authors = [
            author_factory(surname="God"),
            author_factory(surname="Jesus"),
            author_factory(surname="Holy Spirit"),
        ]
        for author in authors:
            author.save()
        return authors

    @pytest.fixture
    def mock_book(self, book_factory, mock_authors, book_author_factory):  # noqa: F811
        mock_book = book_factory(title="The Bible")
        mock_book.save()
        mock_book.add_author(mock_authors[0], order=1)
        return mock_book

    def test_book_display(self, mock_book):
        assert str(mock_book) == "God, The Bible"

    def test_two_authors(self, mock_book, mock_authors):
        mock_book.add_author(mock_authors[1], order=2)
        assert str(mock_book) == "God and Jesus, The Bible"

    def test_three_authors(self, mock_book, mock_authors):
        mock_book.add_author(mock_authors[1], order=2)
        mock_book.add_author(mock_authors[2], order=3)
        assert str(mock_book) == "God, Jesus, and Holy Spirit, The Bible"
