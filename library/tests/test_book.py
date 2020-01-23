from unittest.mock import PropertyMock, patch

import pytest

from library.models import *


@pytest.mark.django_db
class TestBook:
    @pytest.fixture
    def mock_book(self):
        mock_book = Book(title="The Bible")
        mock_author = Author(surname="God")
        mock_book.save()
        mock_author.save()
        authorship = BookAuthor(book=mock_book, author=mock_author)
        authorship.save()

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

    @patch(
        "library.models.Book.all_authors",
        new=PropertyMock(return_value=["Smithee, A.", "Other, A.N."]),
    )
    def test_two_authors(self, mock_book):
        assert mock_book.citation == "Smithee, A. and Other, A.N., The Bible"

    @patch(
        "library.models.Book.all_authors",
        new=PropertyMock(return_value=["Smithee, A.", "Other, A.N.", "Smoth, B."]),
    )
    def test_three_authors(self, mock_book):
        assert (
            mock_book.citation == "Smithee, A., Other, A.N., and Smoth, B., The Bible"
        )
