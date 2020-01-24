import pytest

from library.factories import *
from library.models import *


@pytest.mark.django_db
class TestBook:
    @pytest.fixture
    def mock_book(self, book_factory, author_factory, book_author_factory):
        mock_book = book_factory(title="The Bible")
        mock_author = author_factory(surname="God")
        mock_book.save()
        mock_author.save()
        mock_book.add_author(mock_author)
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

    def test_two_authors(self, mock_book, author_factory):
        second_author = author_factory(surname="Jesus")
        second_author.save()
        mock_book.add_author(second_author)
        assert mock_book.citation == "God and Jesus, The Bible"

    def test_three_authors(self, mock_book, author_factory):
        second_author = author_factory(surname="Jesus")
        third_author = author_factory(surname="Holy Spirit")
        second_author.save()
        third_author.save()
        mock_book.add_author(second_author)
        mock_book.add_author(third_author)
        assert mock_book.citation == "God, Jesus, and Holy Spirit, The Bible"
