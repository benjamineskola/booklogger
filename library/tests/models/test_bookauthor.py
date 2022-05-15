import pytest


@pytest.mark.django_db
class TestBookAuthor:
    @pytest.fixture
    def mock_book(self, book_factory):
        mock_book = book_factory(title="Autobiography")
        mock_book.save()
        return mock_book

    @pytest.fixture
    def mock_author(self, mock_authors):
        return mock_authors[0]

    @pytest.fixture
    def mock_authors(self, author_factory):
        authors = [
            author_factory(surname="Smithee", forenames="Alan"),
            author_factory(surname="Smithee", forenames="Boris"),
        ]
        authors[0].save()
        authors[1].save()
        return authors

    def test_add_author(self, mock_book, mock_author):
        assert len(mock_book.authors) == 0
        mock_book.add_author(mock_author)
        assert len(mock_book.authors) == 1

    def test_add_two_authors(self, mock_book, mock_authors):
        assert len(mock_book.authors) == 0
        mock_book.add_author(mock_authors[0])
        mock_book.add_author(mock_authors[1])
        assert len(mock_book.authors) == 2

    def test_add_same_author_twice(self, mock_book, mock_author):
        assert len(mock_book.authors) == 0
        mock_book.add_author(mock_author)
        mock_book.add_author(mock_author)
        assert len(mock_book.authors) == 1

    def test_add_author_and_role(self, mock_book, mock_authors):
        mock_book.add_author(mock_authors[0])
        mock_book.add_author(mock_authors[1])
        assert (
            mock_book.display_details
            == "Alan Smithee and Boris Smithee, _Autobiography_"
        )

    def test_author_role_none(self, mock_book, mock_author):
        mock_book.add_author(mock_author)
        assert mock_author.role_for_book(mock_book) == ""
        assert mock_author.attribution_for(mock_book, True) == "Smithee, A."

    def test_author_role_simple(self, mock_book, mock_author):
        mock_book.add_author(mock_author, role="introduction")
        assert mock_author.role_for_book(mock_book) == "introduction"
        assert (
            mock_author.attribution_for(mock_book, True) == "Smithee, A. (introduction)"
        )

    def test_author_role_editor_abbr(self, mock_book, mock_author):
        mock_book.add_author(mock_author, role="editor")
        assert mock_author.role_for_book(mock_book) == "editor"
        assert mock_author.display_role_for_book(mock_book) == "ed."
        assert mock_author.attribution_for(mock_book, True) == "Smithee, A. (ed.)"
