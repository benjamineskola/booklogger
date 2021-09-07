import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from library.factories import user_factory  # noqa: F401


@pytest.fixture
def user(user_factory):  # noqa: F811
    if not User.objects.count():
        user_factory(username="ben").save()
    return User.objects.first()


@pytest.fixture(autouse=True)
def get_response(user):
    def _get(view, qs="", **kwargs):
        url = "/"  # doesn't matter — ignored in practice
        if qs:
            url += "?" + qs.lstrip("?")

        req = RequestFactory().get(url)
        req.user = user
        return view.as_view()(req, **kwargs)

    yield _get
