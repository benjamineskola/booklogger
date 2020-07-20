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
            author_factory(),
            author_factory(),
            author_factory(),
            author_factory(),
        ]
        for author in authors:
            author.save()
        return authors

    @pytest.fixture
    def mock_book(self, book_factory, mock_authors, book_author_factory):  # noqa: F811
        mock_book = book_factory()
        mock_book.save()
        mock_book.add_author(mock_authors[0], order=1)
        return mock_book

    def test_book_display(self, mock_authors, mock_book):
        assert str(mock_book) == f"{mock_authors[0]}, {mock_book.display_title}"

    def test_two_authors(self, mock_book, mock_authors):
        mock_book.add_author(mock_authors[1], order=2)
        assert (
            str(mock_book)
            == f"{mock_authors[0]} and {mock_authors[1]}, {mock_book.display_title}"
        )

    def test_three_authors(self, mock_book, mock_authors):
        mock_book.add_author(mock_authors[1], order=2)
        mock_book.add_author(mock_authors[2], order=3)
        assert (
            str(mock_book)
            == f"{mock_authors[0]}, {mock_authors[1]}, and {mock_authors[2]}, {mock_book.display_title}"
        )

    def test_four_authors(self, mock_book, mock_authors):
        mock_book.add_author(mock_authors[1], order=2)
        mock_book.add_author(mock_authors[2], order=3)
        mock_book.add_author(mock_authors[3], order=4)
        assert (
            str(mock_book) == f"{mock_authors[0]} and others, {mock_book.display_title}"
        )
