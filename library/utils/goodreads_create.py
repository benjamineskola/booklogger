#!/usr/bin/env python


import re
from typing import Any, Optional

from library.models import Author, Book


def goodreads_create(
    data: dict[str, Any], query: Optional[str] = None
) -> Optional[Book]:
    goodreads_book = data["best_book"]

    title = goodreads_book["title"].strip()
    series_name = ""
    series_order = None

    if title.endswith(")"):
        title, rest = title.split(" (", 2)
        first_series = rest.split(";")[0]
        series_name, *rest = first_series.split("#")
        series_name = series_name.strip(" ,)")
        if rest:
            try:
                series_order = float(rest[0].strip(")"))
            except ValueError:
                pass

    book = Book(
        title=title,
        series=series_name,
        series_order=series_order,
    )

    book.first_author, created = Author.objects.get_or_create_by_single_name(
        goodreads_book["author"]["name"]
    )

    if query:
        if len(query) == 13 and query.startswith("978"):
            book.isbn = query
        elif re.match(r"^B[A-Z0-9]{9}$", query):
            book.asin = query
            book.edition_format = Book.Format.EBOOK

    book.save()

    return book.update_from_goodreads(data=data)
