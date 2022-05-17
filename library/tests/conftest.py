import os

from pytest_factoryboy import register

from library.factories import AuthorFactory, BookFactory, UserFactory  # noqa: F401

register(AuthorFactory)
register(BookFactory)
register(UserFactory)


if "GOODREADS_KEY" in os.environ:
    del os.environ["GOODREADS_KEY"]
