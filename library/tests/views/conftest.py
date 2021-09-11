import pytest
from django.contrib.auth.models import User
from django.http import QueryDict
from django.test import RequestFactory


@pytest.fixture
def user(user_factory):
    if not User.objects.count():
        user_factory(username="ben").save()
    return User.objects.first()


@pytest.fixture(autouse=True)
def get_response(user):
    def _get(view, get=None, **kwargs):
        url = "/"  # doesn't matter — ignored in practice
        if get:
            q = QueryDict(mutable=True)
            q.update(get)
            url += "?" + q.urlencode()

        req = RequestFactory().get(url)
        req.user = user
        return view.as_view()(req, **kwargs)

    yield _get
