import pytest

from library.models import *


@pytest.mark.django_db
class TestBookAuthor:
    @pytest.fixture
    def mock_book(self):
        mock_book = Book(title="Autobiography")
        mock_book.save()
        return mock_book

    @pytest.fixture
    def mock_author(self):
        mock_author = Author(surname="Smithee", forenames="Alan")
        mock_author.save()
        return mock_author

    def test_author_role_none(self, mock_book, mock_author):
        authorship = BookAuthor(book=mock_book, author=mock_author)
        authorship.save()
        assert mock_author._role_for_book(mock_book) is None

    def test_author_role_simple(self, mock_book, mock_author):
        authorship = BookAuthor(book=mock_book, author=mock_author)
        authorship.role = "introduction"
        authorship.save()
        assert mock_author._role_for_book(mock_book) == "introduction"

    def test_author_role_editor_abbr(self, mock_book, mock_author):
        authorship = BookAuthor(book=mock_book, author=mock_author)
        authorship.role = "editor"
        authorship.save()
        assert mock_author._role_for_book(mock_book) == "ed."
