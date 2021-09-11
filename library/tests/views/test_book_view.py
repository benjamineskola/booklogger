import pytest

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
    def test_currently_reading(self, get_response, book_factory):
        view = CurrentlyReadingView
        book = book_factory()
        book.save()

        resp = get_response(view)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 0

        book.start_reading()

        resp = get_response(view)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 1

        book.finish_reading()

        resp = get_response(view)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 0

    def test_read(self, get_response, book_factory):
        view = ReadView
        book = book_factory()
        book.save()

        resp = get_response(view)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 0

        book.start_reading()

        resp = get_response(view)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 0

        book.finish_reading()

        resp = get_response(view)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 1

    def test_toread(self, get_response, book_factory, user):
        view = UnreadIndexView

        resp = get_response(view)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 0

        book = book_factory()
        book.owned_by = user
        book.save()

        resp = get_response(view)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 1
        book.start_reading()

        resp = get_response(view)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 0

        book.finish_reading()

        resp = get_response(view)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 0

    def test_format_filters(self, get_response, book_factory, user):
        view = OwnedIndexView

        book_ebook = book_factory()
        book_ebook.owned_by = user
        book_ebook.edition_format = Book.Format["EBOOK"]
        book_ebook.save()
        book_paperback = book_factory()
        book_paperback.owned_by = user
        book_paperback.edition_format = Book.Format["PAPERBACK"]
        book_paperback.save()

        resp = get_response(view)
        assert resp.status_code == 200
        assert book_ebook in resp.context_data["object_list"]
        assert book_paperback in resp.context_data["object_list"]

        resp = get_response(view, format="ebook")
        assert resp.status_code == 200
        assert book_ebook in resp.context_data["object_list"]
        assert book_paperback not in resp.context_data["object_list"]

        resp = get_response(view, format="paperback")
        assert resp.status_code == 200
        assert book_ebook not in resp.context_data["object_list"]
        assert book_paperback in resp.context_data["object_list"]

        resp = get_response(view, format="physical")
        assert resp.status_code == 200
        assert book_ebook not in resp.context_data["object_list"]
        assert book_paperback in resp.context_data["object_list"]

    def test_tag_filters(self, get_response, book_factory, user):
        view = IndexView
        book_fiction = book_factory()
        book_fiction.tags = ["fiction"]
        book_fiction.save()
        book_nonfiction = book_factory()
        book_nonfiction.tags = ["non-fiction"]
        book_nonfiction.save()

        resp = get_response(view)
        assert resp.status_code == 200
        assert book_fiction in resp.context_data["object_list"]
        assert book_nonfiction in resp.context_data["object_list"]

        resp = get_response(view, "tags=fiction")
        assert resp.status_code == 200
        assert book_fiction in resp.context_data["object_list"]
        assert book_nonfiction not in resp.context_data["object_list"]

        resp = get_response(view, "tags=non-fiction")
        assert resp.status_code == 200
        assert book_fiction not in resp.context_data["object_list"]
        assert book_nonfiction in resp.context_data["object_list"]
