import pytest
from pytest_factoryboy import register

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
