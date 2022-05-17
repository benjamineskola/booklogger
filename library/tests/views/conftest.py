import pytest
from django.http import QueryDict
from django.test import RequestFactory


@pytest.fixture(autouse=True)
def get_response(user):
    def _get(view, status_code=200, get=None, **kwargs):
        url = "/"  # doesn't matter — ignored in practice
        if get:
            q = QueryDict(mutable=True)
            q.update(get)
            url += "?" + q.urlencode()

        req = RequestFactory().get(url)
        req.user = user

        resp = view.as_view()(req, **kwargs)
        assert resp.status_code == status_code
        return resp

    yield _get
