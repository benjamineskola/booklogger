#!/usr/bin/env python

from typing import Any

from library.models import Author, Book


def goodreads_create(data: dict[str, Any]) -> Book:
    data["title"] = data["title"].strip()

    if data["title"].endswith(")"):
        data["title"], rest = data["title"].split(" (", 2)
        first_series = rest.split(";")
        data["series"], *rest = first_series[0].split("#")
        data["series"] = data["series"].strip(" ,)")
        if rest:
            try:
                data["series_order"] = float(rest[0].strip(")"))
            except ValueError:
                pass
    print(data)

    book, book_created = Book.objects.get_or_create(
        title__iexact=data["title"],
        first_author__surname__iendswith=data["authors"][0].rsplit(" ", 1)[-1],
    )

    if book_created:
        book.first_author, created = Author.objects.get_or_create_by_single_name(
            data["authors"][0]
        )

    book.update(data)
    book.save()

    for order, name in enumerate(data["authors"][1:], start=1):
        author, created = Author.objects.get_or_create_by_single_name(name.strip())
        if author not in book.additional_authors.all():
            book.add_author(author, order=order)

    return book
