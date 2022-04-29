from contextlib import suppress
from typing import Any

from django.db.models import Q

from library.models import Author, Book
from library.utils import smarten


def book(data: dict[str, Any]) -> tuple[Book, bool, list[tuple[Author, bool]]]:
    data["title"] = data["title"].strip()

    if data["title"].endswith(")"):
        data["title"], rest = data["title"].split(" (", 1)
        first_series = rest.split(";")
        data["series"], *rest = first_series[0].split("#")
        data["series"] = data["series"].strip(" ,)")
        if rest:
            with suppress(ValueError):
                data["series_order"] = float(rest[0].strip(")"))

    new_book, book_created = Book.objects.filter(
        Q(title__iexact=data["title"]) | Q(title__iexact=smarten(data["title"]))
    ).get_or_create(
        first_author__surname__iendswith=data["authors"][0][0].rsplit(" ", 1)[-1],
    )

    authors = []
    if book_created:
        new_book.first_author, created = Author.objects.get_or_create_by_single_name(
            data["authors"][0][0]
        )
        if data["authors"][0][1]:
            data["first_author_role"] = data["authors"][0][1]
        authors.append((new_book.first_author, created))

    new_book.update(data)
    new_book.slug = ""
    new_book.save()

    for order, (name, role) in enumerate(data["authors"][1:], start=1):
        author, created = Author.objects.get_or_create_by_single_name(name.strip())
        if author not in new_book.additional_authors.all():
            author.slug = ""
            author.save()
            new_book.add_author(author, order=order, role=role)
        authors.append((author, created))

    return (new_book, book_created, authors)
