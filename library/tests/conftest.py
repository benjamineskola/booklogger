import pytest
from pytest_factoryboy import register

from library.factories import (  # noqa: F401
    AuthorFactory,
    BookFactory,
    TagFactory,
    UserFactory,
)

register(AuthorFactory)
register(BookFactory)
register(TagFactory)
register(UserFactory)


@pytest.fixture(autouse=True)
def unset_goodreads_key(settings):
    settings.GOODREADS_KEY = None


@pytest.fixture
def goodreads_key(settings):
    settings.GOODREADS_KEY = "TEST_FAKE"
