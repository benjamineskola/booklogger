import pytest

from library.models import Book


@pytest.mark.django_db
class TestBook:
    @pytest.fixture(scope="session")
    def django_db_setup(django_db_setup, django_db_blocker):
        """Test session DB setup."""
        from django.db import connection

        with django_db_blocker.unblock():
            with connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    @pytest.fixture
    def mock_authors(self, author_factory):
        authors = [
            author_factory(),
            author_factory(),
            author_factory(),
            author_factory(),
        ]
        for author in authors:
            author.save()
        return authors

    @pytest.fixture
    def mock_book(self, book_factory, mock_authors, book_author_factory):
        mock_book = book_factory()
        mock_book.save()
        mock_book.add_author(mock_authors[0], order=1)
        return mock_book

    @pytest.fixture
    def mock_book_with_author(self, mock_book, mock_authors):
        book = mock_book
        book.add_author(mock_authors[0])
        return book

    def test_book_display(self, mock_authors, mock_book):
        assert (
            mock_book.display_details
            == f"{mock_authors[0]}, *{mock_book.display_title}*"
        )

    def test_two_authors(self, mock_book, mock_authors):
        mock_book.add_author(mock_authors[1], order=2)
        assert (
            mock_book.display_details
            == f"{mock_authors[0]} and {mock_authors[1]}, *{mock_book.display_title}*"
        )

    def test_three_authors(self, mock_book, mock_authors):
        mock_book.add_author(mock_authors[1], order=2)
        mock_book.add_author(mock_authors[2], order=3)
        assert (
            mock_book.display_details
            == f"{mock_authors[0]}, {mock_authors[1]}, and {mock_authors[2]}, *{mock_book.display_title}*"
        )

    def test_four_authors(self, mock_book, mock_authors):
        mock_book.add_author(mock_authors[1], order=2)
        mock_book.add_author(mock_authors[2], order=3)
        mock_book.add_author(mock_authors[3], order=4)
        assert (
            mock_book.display_details
            == f"{mock_authors[0]} and others, *{mock_book.display_title}*"
        )

    def test_search_by_title(self, mock_book_with_author):
        book = mock_book_with_author
        results = Book.objects.search(book.title)
        assert book in results

    def test_search_by_author(self, mock_book_with_author):
        book = mock_book_with_author
        results = Book.objects.search(book.first_author.surname)
        assert book in results
