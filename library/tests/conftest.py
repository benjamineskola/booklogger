import pytest
from pytest_factoryboy import register

from booklogger import settings
from library.factories import AuthorFactory, BookFactory, TagFactory, UserFactory

register(AuthorFactory)
register(BookFactory)
register(TagFactory)
register(UserFactory)


@pytest.fixture(autouse=True)
def _unset_goodreads_key(settings):
    settings.GOODREADS_KEY = None


@pytest.fixture()
def _goodreads_key(settings):
    settings.GOODREADS_KEY = "TEST_FAKE"


@pytest.fixture()
def read_book(book, transactional_db):  # noqa: ARG001
    book.start_reading()
    book.finish_reading()

    return book


@pytest.fixture()
def read_book_factory(book_factory, *args, **kwargs):  # noqa: ARG001
    def _book_factory(*args, **kwargs):
        book = book_factory(*args, **kwargs)
        book.start_reading()
        book.finish_reading()
        return book

    return _book_factory


@pytest.fixture(scope="session")
def django_db_modify_db_settings(  # noqa: PT004
    request, worker_id, django_db_modify_db_settings  # noqa: ARG001
):
    settings.DATABASES["default"] = settings.DATABASES["test"]
