import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from library.factories import user_factory  # noqa: F401


@pytest.fixture
def user(user_factory):  # noqa: F811
    if not User.objects.count():
        user_factory(username="ben").save()
    return User.objects.first()


@pytest.fixture
def get(user):
    def _get(url):
        req = RequestFactory().get(url)
        req.user = user
        return req

    yield _get
