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
        mock_book.add_author(mock_author)
        assert mock_author._role_for_book(mock_book) is None

    def test_author_role_simple(self, mock_book, mock_author):
        mock_book.add_author(mock_author, role="introduction")
        assert mock_author._role_for_book(mock_book) == "introduction"

    def test_author_role_editor_abbr(self, mock_book, mock_author):
        mock_book.add_author(mock_author, role="editor")
        assert mock_author._role_for_book(mock_book) == "ed."
