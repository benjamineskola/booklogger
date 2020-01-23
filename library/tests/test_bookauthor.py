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

    @pytest.fixture
    def mock_authors(self):
        author1 = Author(surname="Smithee", forenames="Alan")
        author2 = Author(surname="Smithee", forenames="Alan")
        author1.save()
        author2.save()
        return [author1, author2]

    def test_add_author(self, mock_book, mock_author):
        assert mock_book.authors.count() == 0
        mock_book.add_author(mock_author)
        assert mock_book.bookauthor_set.count() == 1

    def test_add_two_authors(self, mock_book, mock_authors):
        author1, author2 = mock_authors
        assert mock_book.authors.count() == 0
        mock_book.add_author(author1)
        mock_book.add_author(author2)
        assert mock_book.bookauthor_set.count() == 2

    def test_add_same_author_twice(self, mock_book, mock_author):
        assert mock_book.authors.count() == 0
        mock_book.add_author(mock_author)
        mock_book.add_author(mock_author)
        assert mock_book.bookauthor_set.count() == 1

    def test_author_role_none(self, mock_book, mock_author):
        mock_book.add_author(mock_author)
        assert mock_author._role_for_book(mock_book) == ""
        assert mock_author.attribution_for(mock_book) == "Smithee, A."

    def test_author_role_simple(self, mock_book, mock_author):
        mock_book.add_author(mock_author, role="introduction")
        assert mock_author._role_for_book(mock_book) == "introduction"
        assert mock_author.attribution_for(mock_book) == "Smithee, A. (introduction)"

    def test_author_role_editor_abbr(self, mock_book, mock_author):
        mock_book.add_author(mock_author, role="editor")
        assert mock_author._role_for_book(mock_book) == "ed."
        assert mock_author.attribution_for(mock_book) == "Smithee, A. (ed.)"
