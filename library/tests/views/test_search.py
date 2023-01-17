import pytest


@pytest.mark.django_db()
class TestSearch:
    def test_search_form(self, client):
        resp = client.get("/search/")

        assert not resp.context_data["authors"]
        assert not resp.context_data["books"]
        assert (
            b'<input class="form-control mr-sm-2" type="search" placeholder="Search" aria-label="Search" name="query">'
            in resp.content
        )

    def test_search_query_book(self, client, book):
        resp = client.get("/search/", {"query": book.title})
        assert book in resp.context_data["books"]
        assert book.first_author not in resp.context_data["authors"]

    def test_search_query_author(self, client, book):
        resp = client.get("/search/", {"query": str(book.first_author)})
        assert book.first_author in resp.context_data["authors"]
        assert book in resp.context_data["books"]

    def test_search_query_author_book(self, client, author_factory, book_factory):
        book1 = book_factory(title="foo")
        book2 = book_factory(title="bar", first_author=author_factory(surname="foo"))

        resp = client.get("/search/", {"query": "foo"})

        assert book1 in resp.context_data["books"]
        assert book2.first_author in resp.context_data["authors"]
        assert book2 in resp.context_data["books"]
        assert book1.first_author not in resp.context_data["authors"]

    def test_search_isbn(self, client, book):
        resp = client.get("/search/", {"query": book.isbn})
        assert resp.headers["Location"] == book.get_absolute_url()
