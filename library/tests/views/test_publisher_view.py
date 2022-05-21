import pytest


@pytest.mark.django_db
class TestPublisher:
    def test_publisher_list(self, book_factory, client):
        book_factory(publisher="Foo")

        resp = client.get("/publishers/")
        assert "Foo" in resp.context_data["publishers"]
