import pytest

from library.models import Book, Tag
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

    def test_owned(self, get_response, book, user):
        view = OwnedIndexView

        resp = get_response(view)
        assert len(resp.context_data["object_list"]) == 0

        book.owned_by = user
        book.save()

        resp = get_response(view)
        assert len(resp.context_data["object_list"]) == 1

    @pytest.mark.parametrize("format", ["EBOOK", "PAPERBACK", "HARDBACK", "WEB"])
    @pytest.mark.parametrize(
        "view_format", ["EBOOK", "PAPERBACK", "HARDBACK", "WEB", "PHYSICAL"]
    )
    def test_format_filters(self, get_response, book_factory, format, view_format):
        book = book_factory(edition_format=Book.Format[format])

        resp = get_response(IndexView, format=view_format)

        if view_format == format or (
            format in ["PAPERBACK", "HARDBACK"] and view_format == "PHYSICAL"
        ):
            assert book in resp.context_data["object_list"]
        else:
            assert book not in resp.context_data["object_list"]

    @pytest.mark.parametrize("tag", ["fiction", "non-fiction"])
    @pytest.mark.parametrize("view_tag", ["fiction", "non-fiction"])
    def test_tag_filters(self, get_response, book_factory, tag, view_tag):
        book = book_factory(tags=[tag])
        [Tag(name=name).save() for name in ["fiction", "non-fiction"]]

        resp = get_response(IndexView, get={"tags": view_tag})
        if tag == view_tag:
            assert book in resp.context_data["object_list"]
        else:
            assert book not in resp.context_data["object_list"]

    def test_sort_order(self, get_response, book_factory):
        book1 = book_factory(title="AAAAA", first_published=1999)
        book2 = book_factory(title="BBBBB", first_published=2000)

        resp = get_response(IndexView, sort_by="title")
        assert resp.context_data["object_list"][0] == book1
        assert resp.context_data["object_list"][1] == book2

        resp = get_response(IndexView, sort_by="first_published")
        assert resp.context_data["object_list"][0] == book2
        assert resp.context_data["object_list"][1] == book1
