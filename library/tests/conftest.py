import os

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


if "GOODREADS_KEY" in os.environ:
    del os.environ["GOODREADS_KEY"]
