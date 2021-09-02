from django.db.models import Field, Lookup

from .author import Author, AuthorManager  # noqa: F401
from .book import Book, BookAuthor, BookManager, BookQuerySet, Tag  # noqa: F401
from .log_entry import LogEntry, LogEntryQuerySet  # noqa: F401
from .reading_list import ReadingList, ReadingListEntry  # noqa: F401

__all__ = [
    "Author",
    "AuthorManager",
    "Book",
    "BookAuthor",
    "BookManager",
    "BookQuerySet",
    "LogEntry",
    "LogEntryQuerySet",
    "ReadingList",
    "ReadingListEntry",
    "Tag",
]


# from https://docs.djangoproject.com/en/3.1/howto/custom-lookups/
class NotEqual(Lookup):  # type: ignore [type-arg]
    lookup_name = "ne"

    def as_sql(self, compiler, connection):  # type: ignore [no-untyped-def]
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return "%s <> %s" % (lhs, rhs), params


Field.register_lookup(NotEqual)
