import pytest


@pytest.mark.django_db
class TestPublisher:
    def test_publisher_list(self, book_factory, client):
        book_factory(series="Foo")

        resp = client.get("/series/")
        print(resp.context_data)
        assert "Foo" in resp.context_data["all_series"]
