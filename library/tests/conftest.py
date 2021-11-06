import os

from library.factories import (  # noqa: F401
    author_factory,
    book_author_factory,
    book_factory,
    user_factory,
)

if "GOODREADS_KEY" in os.environ:
    del os.environ["GOODREADS_KEY"]
