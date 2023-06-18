from typing import Any

from django.db.models import Field, Lookup

from .api_key import ApiKey
from .author import Author, AuthorManager
from .book import Book, BookAuthor, BookQuerySet, Tag
from .log_entry import LogEntry, LogEntryQuerySet
from .queue import Queue
from .reading_list import ReadingList, ReadingListEntry
from .statistics_report import StatisticsReport

__all__ = [
    "ApiKey",
    "Author",
    "AuthorManager",
    "Book",
    "BookAuthor",
    "BookQuerySet",
    "LogEntry",
    "LogEntryQuerySet",
    "Queue",
    "ReadingList",
    "ReadingListEntry",
    "StatisticsReport",
    "Tag",
]


# from https://docs.djangoproject.com/en/3.1/howto/custom-lookups/
class NotEqual(Lookup):  # type: ignore[type-arg]
    lookup_name = "ne"

    def as_sql(self, compiler: Any, connection: Any) -> tuple[str, Any]:
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return f"{lhs} <> {rhs}", params


# from https://stackoverflow.com/a/59972954
class Like(Lookup):  # type: ignore[type-arg]
    lookup_name = "like"

    def as_sql(self, compiler: Any, connection: Any) -> tuple[str, Any]:
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return f"{lhs} LIKE {rhs}", params


Field.register_lookup(NotEqual)
Field.register_lookup(Like)
