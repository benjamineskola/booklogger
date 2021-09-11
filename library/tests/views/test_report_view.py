import pytest

from library.views.report import IndexView


@pytest.mark.django_db
class TestReportView:
    def test_report_index(self, get_response, book_factory, user):
        book_factory(isbn="", owned_by=user).save()

        resp = get_response(IndexView)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 0

    def test_report_page(self, get_response, book_factory, user):
        book_factory(isbn="", owned_by=user).save()

        resp = get_response(IndexView, page="1")
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 1
