import pytest

from library.views.report import IndexView


@pytest.mark.django_db
class TestReportView:
    def test_report_index(self, get_response, book_factory, user):
        book_factory(isbn="", owned_by=user)

        resp = get_response(IndexView)
        assert len(resp.context_data["object_list"]) == 0
        assert resp.context_data["page_title"] == "Reports"

    def test_report_page(self, get_response, book_factory, user):
        book_factory(isbn="", owned_by=user)

        resp = get_response(IndexView, page="1")
        assert len(resp.context_data["object_list"]) == 1

    @pytest.mark.parametrize("page", range(1, len(IndexView().categories)))
    def test_report_all_pages(self, page, get_response, book_factory, user):
        book_factory(owned_by=user, tags=["non-fiction", "history"])
        resp = get_response(IndexView, page=str(page))
        assert resp.context_data["page_title"] != "Reports"

    def test_report_ordering(self, get_response, book_factory, user):
        book1 = book_factory(title="Book A", page_count=200, isbn="", owned_by=user)
        book2 = book_factory(title="Book B", page_count=100, isbn="", owned_by=user)

        resp = get_response(IndexView, get={"order_by": "title"}, page="1")
        assert list(resp.context_data["object_list"]) == [book1, book2]

        resp = get_response(IndexView, get={"order_by": "page_count"}, page="1")
        assert list(resp.context_data["object_list"]) == [book2, book1]
