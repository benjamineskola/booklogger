import re
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse

from library.models import Book


def index(request: HttpRequest) -> HttpResponse:
    series_books = Book.objects.exclude(series="").filter(
        private__in=([True, False] if request.user.is_authenticated else [False])
    )

    counts: dict[str, dict[str, set[Any]]] = {}
    for book in series_books:
        series = book.series
        if series not in counts:
            counts[series] = {"books": set(), "authors": set()}

        counts[series]["books"].add(book)

        for author in book.authors:
            counts[series]["authors"].add(author)

    sorted_series = dict(
        sorted(
            counts.items(), key=lambda s: str(re.sub(r"^(A|The) (.*)", r"\2, \1", s[0]))
        )
    )

    return TemplateResponse(
        request,
        "series_list.html",
        {"all_series": sorted_series, "series_count": series_books.count()},
    )
