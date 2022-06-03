import pytest

from library.models import Book, Tag


@pytest.mark.django_db
class TestBook:
    def test_currently_reading(self, client, book):
        resp = client.get("/")
        assert len(resp.context_data["object_list"]) == 0

        book.start_reading()

        resp = client.get("/")
        assert len(resp.context_data["object_list"]) == 1

        book.finish_reading()

        resp = client.get("/")
        assert len(resp.context_data["object_list"]) == 0

    def test_read(self, client, book):
        resp = client.get("/books/read/")
        assert len(resp.context_data["object_list"]) == 0

        book.start_reading()

        resp = client.get("/books/read/")
        assert len(resp.context_data["object_list"]) == 0

        book.finish_reading()

        resp = client.get("/books/read/")
        assert len(resp.context_data["object_list"]) == 1

    def test_toread(self, client, book, user):
        resp = client.get("/books/toread/")
        assert len(resp.context_data["object_list"]) == 0

        book.owned_by = user
        book.save()

        resp = client.get("/books/toread/")
        assert len(resp.context_data["object_list"]) == 1
        book.start_reading()

        resp = client.get("/books/toread/")
        assert len(resp.context_data["object_list"]) == 0

        book.finish_reading()

        resp = client.get("/books/toread/")
        assert len(resp.context_data["object_list"]) == 0

    def test_owned(self, client, book, user):
        resp = client.get("/books/owned/")
        assert len(resp.context_data["object_list"]) == 0

        book.owned_by = user
        book.save()

        resp = client.get("/books/owned/")
        assert len(resp.context_data["object_list"]) == 1

    @pytest.mark.parametrize("format", ["EBOOK", "PAPERBACK", "HARDBACK", "WEB"])
    @pytest.mark.parametrize(
        "view_format", ["EBOOK", "PAPERBACK", "HARDBACK", "WEB", "PHYSICAL"]
    )
    def test_format_filters(self, client, book_factory, format, view_format):
        book = book_factory(edition_format=Book.Format[format])

        resp = client.get(f"/books/{view_format.lower()}/")

        if view_format == format or (
            format in ["PAPERBACK", "HARDBACK"] and view_format == "PHYSICAL"
        ):
            assert book in resp.context_data["object_list"]
        else:
            assert book not in resp.context_data["object_list"]

    @pytest.mark.parametrize("tag", ["fiction", "non-fiction"])
    @pytest.mark.parametrize("view_tag", ["fiction", "non-fiction"])
    def test_tag_filters(self, client, book_factory, tag, view_tag):
        book = book_factory(tags_list=[tag])
        [Tag(name=name).save() for name in ["fiction", "non-fiction"]]

        resp = client.get("/books/", {"tags": view_tag})
        if tag == view_tag:
            assert book in resp.context_data["object_list"]
        else:
            assert book not in resp.context_data["object_list"]

    def test_sort_order(self, client, book_factory):
        book1 = book_factory(title="AAAAA", first_published=1999)
        book2 = book_factory(title="BBBBB", first_published=2000)

        resp = client.get("/books/", {"sort_by": "title"})
        assert resp.context_data["object_list"][0] == book1
        assert resp.context_data["object_list"][1] == book2

        resp = client.get("/books/", {"sort_by": "first_published"})
        assert resp.context_data["object_list"][0] == book2
        assert resp.context_data["object_list"][1] == book1

    def test_start_reading(self, admin_client, book):
        admin_client.post(f"{book.get_absolute_url()}start/")
        assert book.currently_reading

    def test_finish_reading(self, admin_client, book):
        book.start_reading()
        admin_client.post(f"{book.get_absolute_url()}finish/")
        assert book.read

    def test_update_progress_percentage(self, admin_client, book):
        book.start_reading()
        admin_client.post(
            f"{book.get_absolute_url()}update/",
            {"progress_type": "percentage", "value": 50},
        )
        assert book.log_entries.last().progress_percentage == 50

    def test_update_progress_pages(self, admin_client, book_factory):
        book = book_factory(page_count=500)
        book.start_reading()
        admin_client.post(
            f"{book.get_absolute_url()}update/",
            {"progress_type": "pages", "value": 250},
        )
        assert book.log_entries.last().progress_page == 250
        assert book.log_entries.last().progress_percentage == 50

    def test_add_tags(self, admin_client, book):
        admin_client.post(f"{book.get_absolute_url()}add_tags/", {"tags": "foo,bar"})
        book.refresh_from_db()
        assert book.tags == ["bar", "foo"]

    def test_add_tags_noop(self, admin_client, book_factory):
        book = book_factory(tags_list=["foo"])
        resp = admin_client.post(
            f"{book.get_absolute_url()}add_tags/", {"tags": "foo,bar"}
        )
        book.refresh_from_db()
        assert book.tags == ["bar", "foo"]
        assert resp.content == b'{"tags": ["bar"]}'

    def test_remove_tags(self, admin_client, book_factory):
        book = book_factory(tags_list=["foo", "bar"])
        admin_client.post(f"{book.get_absolute_url()}remove_tags/", {"tags": "foo"})
        book.refresh_from_db()
        assert book.tags == ["bar"]

    def test_mark_owned(self, admin_client, book, user):
        admin_client.post(f"{book.get_absolute_url()}mark_owned/")
        book.refresh_from_db()
        assert book.owned

    def test_mark_read_sometime(self, admin_client, book):
        admin_client.post(f"{book.get_absolute_url()}mark_read_sometime/")
        book.refresh_from_db()
        assert book.read

    def test_rate(self, admin_client, book, user):
        admin_client.post(f"{book.get_absolute_url()}rate/", {"rating": 5})
        book.refresh_from_db()
        assert book.rating == 5
