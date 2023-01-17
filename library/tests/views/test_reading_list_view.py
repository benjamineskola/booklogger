import pytest

from library.models import ReadingList


@pytest.mark.django_db()
class TestReadingList:
    def test_index(self, book_factory, client):  # noqa: ARG002
        reading_list = ReadingList()
        reading_list.save()

        resp = client.get("/lists/")
        assert reading_list in resp.context_data["object_list"]

    def test_detail(self, book_factory, client):
        reading_list = ReadingList()
        reading_list.save()
        book1 = book_factory()
        book2 = book_factory()
        reading_list.books.add(book1)

        resp = client.get(f"/list/{reading_list.id}/")
        assert book1 in resp.context_data["object"].books.all()
        assert book2 not in resp.context_data["object"].books.all()
