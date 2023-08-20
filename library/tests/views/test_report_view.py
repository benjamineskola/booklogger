import pytest

from library.models import Tag
from library.views.report import IndexView


@pytest.mark.django_db()
class TestReportView:
    def test_report_admin_only(self, client):
        assert client.get("/report/").status_code == 302
        assert client.get("/report/1/").status_code == 302

    def test_report_index(self, admin_client, book_factory, user):
        book_factory(isbn="", owned_by=user)

        resp = admin_client.get("/report/")
        assert len(resp.context_data["object_list"]) == 0
        assert resp.context_data["page_title"] == "Reports"

    def test_report_page(self, admin_client, book_factory, user):
        book_factory(isbn="", owned_by=user)

        resp = admin_client.get("/report/1/")
        assert len(resp.context_data["object_list"]) == 1

    @pytest.mark.parametrize("page", range(1, len(IndexView().categories)))
    def test_report_all_pages(self, page, admin_client, book, user):  # noqa: ARG002
        book.tags.set(
            (Tag.objects.get(name="non-fiction"), Tag.objects.get(name="history"))
        )
        resp = admin_client.get(f"/report/{page}/")
        assert resp.context_data["page_title"] != "Reports"

    def test_report_ordering(self, admin_client, book_factory, user):
        book1 = book_factory(title="Book A", page_count=200, isbn="", owned_by=user)
        book2 = book_factory(title="Book B", page_count=100, isbn="", owned_by=user)

        resp = admin_client.get("/report/1/", {"order_by": "title"})
        assert list(resp.context_data["object_list"]) == [book1, book2]

        resp = admin_client.get("/report/1/", {"order_by": "page_count"})
        assert list(resp.context_data["object_list"]) == [book2, book1]

    def test_tag_report(self, admin_client, book_factory, tag_factory):
        base_tag = tag_factory(name="non-fiction")
        base_tag.children.add(tag_factory(name="history"))
        base_tag.children.add(tag_factory(name="politics"))

        book1 = book_factory()
        book1.tags.set((Tag.objects.get(name="history"),))

        book2 = book_factory()
        book2.tags.set(
            (Tag.objects.get(name="history"), Tag.objects.get(name="politics"))
        )

        resp = admin_client.get("/report/tags/")

        assert book1 in resp.context_data["results"]["history"]
        assert book1 not in resp.context_data["results"]["politics"]
        assert book2 in resp.context_data["results"]["history"]
        assert book2 in resp.context_data["results"]["politics"]

    def test_tag_related_report(self, admin_client, book_factory, tag_factory):
        base_tag = tag_factory(name="non-fiction")
        base_tag.children.add(tag_factory(name="history"))
        base_tag.children.add(tag_factory(name="politics"))
        base_tag.children.add(tag_factory(name="philosophy"))

        book1 = book_factory()
        book1.tags.set(
            (Tag.objects.get(name="history"), Tag.objects.get(name="politics"))
        )
        book2 = book_factory()
        book2.tags.set((Tag.objects.get(name="philosophy"),))

        resp = admin_client.get("/report/tags/related/")
        results = resp.context_data["results"]

        assert "history" in results["politics"]
        assert "politics" in results["history"]

        assert "philosophy" not in results["politics"]
        assert "philosophy" not in results["history"]
        assert "history" not in results["philosophy"]
        assert "politics" not in results["philosophy"]

    def test_detached_author_report(self, admin_client, author_factory, book_factory):
        author1 = author_factory()
        author2 = author_factory()
        book_factory(first_author=author1)

        resp = admin_client.get("/report/authors/")
        assert author1 not in resp.context_data["object_list"]
        assert author2 in resp.context_data["object_list"]
