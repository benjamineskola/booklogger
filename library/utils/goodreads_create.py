#!/usr/bin/env python

from typing import Any, Optional

from library.models import Author, Book


def goodreads_create(data: dict[str, Any]) -> Optional[Book]:
    title = data["title"].strip()
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
        data["authors"][0]
    )

    book.save()

    for name in data["authors"][1:]:
        author, created = Author.objects.get_or_create_by_single_name(name)
        book.additional_authors.add(author)

    return book.update(data)
