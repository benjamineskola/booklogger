import pytest

from library.models import Book, LogEntry


@pytest.mark.django_db
class TestBook:
    @pytest.fixture(scope="session")
    def django_db_setup(self, django_db_setup, django_db_blocker):
        """Test session DB setup."""
        from django.db import connection

        with django_db_blocker.unblock(), connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    @pytest.fixture
    def mock_authors(self, author_factory):
        return author_factory.create_batch(4)

    def test_book_display(self, author, book):
        book.first_author = author
        assert book.display_details == f"{author}, _{book.display_title}_"

    def test_two_authors(self, book, mock_authors):
        book.first_author = mock_authors[0]
        book.add_author(mock_authors[1], order=2)
        assert (
            book.display_details
            == f"{mock_authors[0]} and {mock_authors[1]}, _{book.display_title}_"
        )

    def test_three_authors(self, book, mock_authors):
        book.first_author = mock_authors[0]
        book.add_author(mock_authors[1], order=2)
        book.add_author(mock_authors[2], order=3)
        assert (
            book.display_details
            == f"{mock_authors[0]}, {mock_authors[1]}, and {mock_authors[2]}, _{book.display_title}_"
        )

    def test_four_authors(self, book, mock_authors):
        book.first_author = mock_authors[0]
        book.add_author(mock_authors[1], order=2)
        book.add_author(mock_authors[2], order=3)
        book.add_author(mock_authors[3], order=4)
        assert (
            book.display_details
            == f"{mock_authors[0]} and others, _{book.display_title}_"
        )

    def test_editor(self, book):
        book.first_author_role = "editor"
        assert (
            book.display_details
            == f"_{book.display_title}_, ed. by {book.first_author}"
        )

    def test_author_and_editor(self, book, author_factory):
        author = author_factory()
        book.add_author(author, order=2, role="editor")
        assert (
            book.display_details
            == f"{book.first_author}, _{book.display_title}_, ed. by {author}"
        )

    def test_search_by_title(self, book):
        results = Book.objects.search(book.title)
        assert book in results

    def test_search_by_author(self, book):
        results = Book.objects.search(book.first_author.surname)
        assert book in results

    @pytest.mark.parametrize("gender", [1, 2])
    @pytest.mark.parametrize("other_gender", [1, 2])
    def test_query_by_gender(self, book_factory, gender, other_gender):
        book = book_factory(first_author__gender=gender)
        book.mark_read_sometime()
        assert book in Book.objects.by_gender(gender)
        assert book.log_entries.first() in LogEntry.objects.by_gender(gender)
        if gender != other_gender:
            assert book not in Book.objects.by_gender(other_gender)
            assert book.log_entries.first() not in LogEntry.objects.by_gender(
                other_gender
            )

        if gender == 1:
            assert book in Book.objects.by_men()
            assert book not in Book.objects.by_women()
        if gender == 2:
            assert book not in Book.objects.by_men()
            assert book in Book.objects.by_women()
