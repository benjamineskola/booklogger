import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory


@pytest.mark.django_db
class TestBook:
    @pytest.fixture
    def factory(self):
        return RequestFactory()

    @pytest.fixture
    def user(self):
        if not User.objects.count():
            User.objects.create(
                username="admin", email="admin@none.invalid", password="s3cr3t"
            )
        return User.objects.first()

    @pytest.fixture
    def get(self, factory, user):
        def _get(url):
            req = factory.get(url)
            req.user = user
            return req

        yield _get

    def test_root(self, get):
        from library.views.book import IndexView

        req = get("/")

        resp = IndexView.as_view()(req)
        assert resp.status_code == 200
        assert len(resp.context_data["object_list"]) == 0
