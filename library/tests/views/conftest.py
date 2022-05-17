import pytest
from django.http import QueryDict
from django.test import RequestFactory


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
