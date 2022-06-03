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


@pytest.fixture
def read_book(book, transactional_db):
    book.start_reading()
    book.finish_reading()

    return book


@pytest.fixture
def read_book_factory(book_factory, *args, **kwargs):
    def _book_factory(*args, **kwargs):
        book = book_factory(*args, **kwargs)
        book.start_reading()
        book.finish_reading()
        return book

    yield _book_factory
