import pytest

from library.models import *


@pytest.mark.django_db
class TestAuthor:
    def test_author_str(self):
        author = Author(surname="Smithee", forenames="Alan")
        assert str(author) == "Smithee, A."

    def test_author_role_none(self):
        book = Book(title="Autobiography")
        author = Author(surname="Smithee", forenames="Alan")
        book.save()
        author.save()
        authorship = BookAuthor(book=book, author=author)
        authorship.save()
        assert author._role_for_book(book) is None

    def test_author_role_simple(self):
        book = Book(title="Autobiography")
        author = Author(surname="Smithee", forenames="Alan")
        book.save()
        author.save()
        authorship = BookAuthor(book=book, author=author)
        authorship.role = "introduction"
        authorship.save()
        assert author._role_for_book(book) == "introduction"

    def test_author_role_editor_abbr(self):
        book = Book(title="Autobiography")
        author = Author(surname="Smithee", forenames="Alan")
        book.save()
        author.save()
        authorship = BookAuthor(book=book, author=author)
        authorship.role = "editor"
        authorship.save()
        assert author._role_for_book(book) == "ed."

    def test_author_initials_multi_names(self):
        author = Author(surname="Smithee", forenames="Alan Allen")
        assert str(author) == "Smithee, A.A."

    def test_author_initials_middle_initial(self):
        author = Author(surname="Smithee", forenames="Alan A.")
        assert str(author) == "Smithee, A.A."

    def test_author_initials_middle_initial_multi(self):
        author = Author(surname="Smithee", forenames="Alan A.A.")
        assert str(author) == "Smithee, A.A.A."

    def test_author_initials_all_initials_1(self):
        author = Author(surname="Smithee", forenames="A.")
        assert str(author) == "Smithee, A."

    def test_author_initials_all_initials_2(self):
        author = Author(surname="Smithee", forenames="A.A.")
        assert str(author) == "Smithee, A.A."
