import pytest

from library.factories import *
from library.models import *


@pytest.mark.django_db
class TestBook:
    @pytest.fixture
    def mock_authors(self, author_factory):
        authors = [
            author_factory(single_name="God"),
            author_factory(single_name="Jesus"),
            author_factory(single_name="Holy Spirit"),
        ]
        for author in authors:
            author.save()
        return authors

    @pytest.fixture
    def mock_book(self, book_factory, mock_authors, book_author_factory):
        mock_book = book_factory(title="The Bible")
        mock_book.save()
        mock_book.add_author(mock_authors[0], order=1)
        return mock_book

    def test_book_display(self, mock_book):
        assert str(mock_book) == "God, The Bible"
        assert mock_book.citation == "God, The Bible"

    def test_book_display_with_date(self, mock_book):
        mock_book.edition_published = 1965
        assert mock_book.citation == "God, The Bible (1965)"

    def test_book_display_with_publisher(self, mock_book):
        mock_book.publisher = "Vatican Books"
        assert mock_book.citation == "God, The Bible (Vatican Books)"

    def test_book_display_with_publisher_and_date(self, mock_book):
        mock_book.publisher = "Vatican Books"
        mock_book.edition_published = 1965
        assert mock_book.citation == "God, The Bible (Vatican Books, 1965)"

    def test_two_authors(self, mock_book, mock_authors):
        mock_book.add_author(mock_authors[1], order=2)
        assert mock_book.citation == "God and Jesus, The Bible"

    def test_three_authors(self, mock_book, mock_authors):
        mock_book.add_author(mock_authors[1], order=2)
        mock_book.add_author(mock_authors[2], order=3)
        assert mock_book.citation == "God, Jesus, and Holy Spirit, The Bible"
