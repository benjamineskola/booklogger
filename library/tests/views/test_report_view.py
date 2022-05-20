import pytest

from library.views.report import IndexView


@pytest.mark.django_db
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
    def test_report_all_pages(self, page, admin_client, book_factory, user):
        book_factory(owned_by=user, tags=["non-fiction", "history"])
        resp = admin_client.get(f"/report/{page}/")
        assert resp.context_data["page_title"] != "Reports"

    def test_report_ordering(self, admin_client, book_factory, user):
        book1 = book_factory(title="Book A", page_count=200, isbn="", owned_by=user)
        book2 = book_factory(title="Book B", page_count=100, isbn="", owned_by=user)

        resp = admin_client.get("/report/1/", {"order_by": "title"})
        assert list(resp.context_data["object_list"]) == [book1, book2]

        resp = admin_client.get("/report/1/", {"order_by": "page_count"})
        assert list(resp.context_data["object_list"]) == [book2, book1]
