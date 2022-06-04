import json

import pytest

from library.models import Book


@pytest.mark.django_db
class TestImporter:
    @pytest.fixture(scope="session")
    def django_db_setup(self, django_db_setup, django_db_blocker):
        """Test session DB setup."""
        from django.db import connection

        with django_db_blocker.unblock(), connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    @pytest.fixture
    def goodreads_mock(self, requests_mock, goodreads_key):
        with open("library/fixtures/wuthering_heights.xml") as file:
            text = file.read()
            requests_mock.get(
                "https://www.goodreads.com/search/index.xml?key=TEST_FAKE&q=Wuthering%20Heights",
                text=text,
            )
            requests_mock.get(
                "https://www.goodreads.com/search/index.xml?key=TEST_FAKE&q=9780199541898",
                text=text,
            )
            requests_mock.get(
                "https://www.goodreads.com/search/index.xml?key=TEST_FAKE&q=B002RI97IO",
                text=text,
            )
        requests_mock.get(
            "https://www.googleapis.com/books/v1/volumes?q=isbn:9780199541898",
            text="{}",
        )

    def test_import_get_without_query(self, admin_client):
        resp = admin_client.get("/book/import/")

        assert b"<input" in resp.content
        assert b"This might be the following books on Goodreads" not in resp.content

        assert not resp.context_data["query"]
        assert not resp.context_data["goodreads_results"]
        assert not resp.context_data["matches"]

    def test_import_get_with_query(self, admin_client, goodreads_mock):
        resp = admin_client.get("/book/import/", {"query": "Wuthering Heights"})
        assert b"This might be the following books on Goodreads" in resp.content
        assert b"Wuthering Heights" in resp.content
        assert resp.context_data["goodreads_results"][0]["title"] == "Wuthering Heights"

    @pytest.mark.parametrize(
        "query_string,expected",
        [
            ("Wuthering Heights", {"isbn": "", "asin": "", "edition_format": 0}),
            (
                "9780199541898",
                {"isbn": "9780199541898", "asin": "", "edition_format": 0},
            ),
            (
                "B002RI97IO",
                {
                    "isbn": "",
                    "asin": "B002RI97IO",
                    "edition_format": Book.Format.EBOOK,
                },
            ),
        ],
    )
    def test_import_post(self, admin_client, goodreads_mock, query_string, expected):
        query = admin_client.get("/book/import/", {"query": query_string})
        resp = admin_client.post(
            "/book/import/",
            {
                "query": query_string,
                "data": json.dumps(query.context_data["goodreads_results"][0]),
            },
        )

        assert resp.status_code == 302
        assert resp.headers["Location"] == "/book/bronte-wuthering-heights/edit/"
        book = Book.objects.get(slug="bronte-wuthering-heights")
        assert book.title == "Wuthering Heights"
        assert book.isbn == expected["isbn"]
        assert book.asin == expected["asin"]
        assert book.edition_format == expected["edition_format"]
