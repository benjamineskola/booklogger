import pytest


@pytest.mark.django_db
class TestBookAuthor:
    @pytest.fixture
    def book(self, book_factory):
        return book_factory(first_author=None, title="Autobiography")

    @pytest.fixture
    def author(self, authors):
        return authors[0]

    @pytest.fixture
    def authors(self, author_factory):
        authors = [
            author_factory(surname="Smithee", forenames="Alan"),
            author_factory(surname="Smithee", forenames="Boris"),
        ]

        return authors

    def test_add_author(self, book, author):
        assert len(book.authors) == 0
        book.add_author(author)
        assert len(book.authors) == 1

    def test_add_two_authors(self, book, authors):
        assert len(book.authors) == 0
        book.first_author = authors[0]
        book.add_author(authors[1])
        assert len(book.authors) == 2

    def test_add_same_author_twice(self, book, author):
        assert len(book.authors) == 0
        book.add_author(author)
        book.add_author(author)
        assert len(book.authors) == 1

    def test_add_author_and_role(self, book, authors):
        book.first_author = authors[0]
        book.add_author(authors[1])
        assert book.display_details == "Alan Smithee and Boris Smithee, _Autobiography_"

    def test_author_role_none(self, book, author):
        book.add_author(author)
        assert author.role_for_book(book) == ""
        assert author.attribution_for(book, True) == "Smithee, A."

    def test_author_role_simple(self, book, author):
        book.add_author(author, role="introduction")
        assert author.role_for_book(book) == "introduction"
        assert author.attribution_for(book, True) == "Smithee, A. (introduction)"

    def test_author_role_editor_abbr(self, book, author):
        book.add_author(author, role="editor")
        assert author.role_for_book(book) == "editor"
        assert author.display_role_for_book(book) == "ed."
        assert author.attribution_for(book, True) == "Smithee, A. (ed.)"
