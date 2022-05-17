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
    def test_currently_reading(self, get_response, book):
        view = CurrentlyReadingView

        resp = get_response(view)
        assert len(resp.context_data["object_list"]) == 0

        book.start_reading()

        resp = get_response(view)
        assert len(resp.context_data["object_list"]) == 1

        book.finish_reading()

        resp = get_response(view)
        assert len(resp.context_data["object_list"]) == 0

    def test_read(self, get_response, book):
        view = ReadView

        resp = get_response(view)
        assert len(resp.context_data["object_list"]) == 0

        book.start_reading()

        resp = get_response(view)
        assert len(resp.context_data["object_list"]) == 0

        book.finish_reading()

        resp = get_response(view)
        assert len(resp.context_data["object_list"]) == 1

    def test_toread(self, get_response, book, user):
        view = UnreadIndexView

        resp = get_response(view)
        assert len(resp.context_data["object_list"]) == 0

        book.owned_by = user
        book.save()

        resp = get_response(view)
        assert len(resp.context_data["object_list"]) == 1
        book.start_reading()

        resp = get_response(view)
        assert len(resp.context_data["object_list"]) == 0

        book.finish_reading()

        resp = get_response(view)
        assert len(resp.context_data["object_list"]) == 0

    def test_format_filters(self, get_response, book_factory, user):
        view = OwnedIndexView

        book_ebook = book_factory(owned_by=user, edition_format=Book.Format["EBOOK"])
        book_paperback = book_factory(
            owned_by=user, edition_format=Book.Format["PAPERBACK"]
        )

        resp = get_response(view)
        assert book_ebook in resp.context_data["object_list"]
        assert book_paperback in resp.context_data["object_list"]

        resp = get_response(view, format="ebook")
        assert book_ebook in resp.context_data["object_list"]
        assert book_paperback not in resp.context_data["object_list"]

        resp = get_response(view, format="paperback")
        assert book_ebook not in resp.context_data["object_list"]
        assert book_paperback in resp.context_data["object_list"]

        resp = get_response(view, format="physical")
        assert book_ebook not in resp.context_data["object_list"]
        assert book_paperback in resp.context_data["object_list"]

    def test_tag_filters(self, get_response, book_factory, user):
        view = IndexView
        book_fiction = book_factory(tags=["fiction"])
        book_nonfiction = book_factory(tags=["non-fiction"])

        resp = get_response(view)
        assert book_fiction in resp.context_data["object_list"]
        assert book_nonfiction in resp.context_data["object_list"]

        resp = get_response(view, get={"tags": "fiction"})
        assert book_fiction in resp.context_data["object_list"]
        assert book_nonfiction not in resp.context_data["object_list"]

        resp = get_response(view, get={"tags": "non-fiction"})
        assert book_fiction not in resp.context_data["object_list"]
        assert book_nonfiction in resp.context_data["object_list"]
