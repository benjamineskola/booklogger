import pytest


@pytest.mark.django_db
class TestLogEntry:
    def test_read_sometime(self, book_factory, client):
        book1 = book_factory()
        book1.mark_read_sometime()
        book2 = book_factory()

        resp = client.get("/books/read/sometime/")
        results = [entry.book for entry in resp.context_data["entries"]]
        assert book1 in results
        assert book2 not in results

    def test_read_by_year(self, book_factory, client):
        book1 = book_factory()
        book1.mark_read_sometime()
        book1.log_entries.update(end_date="2022-01-01 00:00:00+00:00")
        book2 = book_factory()
        book2.mark_read_sometime()
        book3 = book_factory()

        resp = client.get("/books/read/2022/")
        results = [entry.book for entry in resp.context_data["entries"]]
        assert book1 in results
        assert book2 not in results
        assert book3 not in results

    def test_currently_reading(self, book_factory, client):
        book1 = book_factory()
        book1.start_reading()
        book2 = book_factory()
        book2.mark_read_sometime()
        book3 = book_factory()

        resp = client.get("/books/reading/")
        results = [entry.book for entry in resp.context_data["entries"]]
        assert book1 in results
        assert book2 not in results
        assert book3 not in results
