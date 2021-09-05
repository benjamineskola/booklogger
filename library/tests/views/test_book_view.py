import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from library.factories import user_factory  # noqa: F401


@pytest.mark.django_db
class TestBook:
    @pytest.fixture
    def factory(self):
        return RequestFactory()

    @pytest.fixture
    def user(self, user_factory):  # noqa: F811
        if not User.objects.count():
            user_factory().save()
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
