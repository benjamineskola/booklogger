import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from library.factories import book_factory, user_factory  # noqa: F401
from library.models import Book
from library.views.book import (
    CurrentlyReadingView,
    IndexView,
    OwnedIndexView,
    ReadView,
    UnreadIndexView,
)


@pytest.mark.django_db
class TestBook:
    @pytest.fixture
    def factory(self):
        return RequestFactory()

    @pytest.fixture
    def user(self, user_factory):  # noqa: F811
        if not User.objects.count():
            user_factory(username="ben").save()
        return User.objects.first()

    @pytest.fixture
    def get(self, factory, user):
        def _get(url):
            req = factory.get(url)
            req.user = user
            return req

        yield _get

    def test_currently_reading(self, get, book_factory):  # noqa: F811
        view = CurrentlyReadingView.as_view()
        book = book_factory()
        book.save()

        req = get("/")
        resp = view(req)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 0

        book.start_reading()

        req = get("/")
        resp = view(req)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 1

        book.finish_reading()

        req = get("/")
        resp = view(req)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 0

    def test_read(self, get, book_factory):  # noqa: F811
        view = ReadView.as_view()
        book = book_factory()
        book.save()

        req = get("/books/read/")
        resp = view(req)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 0

        book.start_reading()

        req = get("/books/read/")
        resp = view(req)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 0

        book.finish_reading()

        req = get("/books/read/")
        resp = view(req)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 1

    def test_toread(self, get, book_factory, user):  # noqa: F811
        view = UnreadIndexView.as_view()

        req = get("/books/toread/")
        resp = view(req)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 0

        book = book_factory()
        book.owned_by = user
        book.save()

        req = get("/books/toread/")
        resp = view(req)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 1
        book.start_reading()

        req = get("/books/toread/")
        resp = view(req)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 0

        book.finish_reading()

        req = get("/books/toread/")
        resp = view(req)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 0

    def test_format_filters(self, get, book_factory, user):  # noqa: F811
        view = OwnedIndexView.as_view()

        book_ebook = book_factory()
        book_ebook.owned_by = user
        book_ebook.edition_format = Book.Format["EBOOK"]
        book_ebook.save()
        book_paperback = book_factory()
        book_paperback.owned_by = user
        book_paperback.edition_format = Book.Format["PAPERBACK"]
        book_paperback.save()

        req = get("/books/owned/")
        resp = view(req)
        assert resp.status_code == 200
        assert book_ebook in resp.context_data["object_list"]
        assert book_paperback in resp.context_data["object_list"]

        req = get("/books/owned/ebook/")
        resp = view(req, format="ebook")
        assert resp.status_code == 200
        assert book_ebook in resp.context_data["object_list"]
        assert book_paperback not in resp.context_data["object_list"]

        req = get("/books/owned/paperback/")
        resp = view(req, format="paperback")
        assert resp.status_code == 200
        assert book_ebook not in resp.context_data["object_list"]
        assert book_paperback in resp.context_data["object_list"]

        req = get("/books/owned/physical/")
        resp = view(req, format="physical")
        assert resp.status_code == 200
        assert book_ebook not in resp.context_data["object_list"]
        assert book_paperback in resp.context_data["object_list"]

    def test_tag_filters(self, get, book_factory, user):  # noqa: F811
        view = IndexView.as_view()
        book_fiction = book_factory()
        book_fiction.tags = ["fiction"]
        book_fiction.save()
        book_nonfiction = book_factory()
        book_nonfiction.tags = ["non-fiction"]
        book_nonfiction.save()

        req = get("/books/")
        resp = view(req)
        assert resp.status_code == 200
        assert book_fiction in resp.context_data["object_list"]
        assert book_nonfiction in resp.context_data["object_list"]

        req = get("/books/?tags=fiction")
        resp = view(req)
        assert resp.status_code == 200
        assert book_fiction in resp.context_data["object_list"]
        assert book_nonfiction not in resp.context_data["object_list"]

        req = get("/books/?tags=non-fiction")
        resp = view(req)
        assert resp.status_code == 200
        assert book_fiction not in resp.context_data["object_list"]
        assert book_nonfiction in resp.context_data["object_list"]
