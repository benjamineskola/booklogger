import re

from django.shortcuts import render
from library.models import Book


def list(request):
    series_books = Book.objects.exclude(series="")
    counts = {}
    for book in series_books:
        series = book.series
        if series not in counts:
            counts[series] = {"count": 0, "authors": set()}

        counts[series]["count"] += 1

        for author in book.authors:
            counts[series]["authors"].add(author)

    sorted_series = {
        k: v
        for k, v in sorted(
            counts.items(), key=lambda s: re.sub(r"^(A|The) (.*)", r"\2, \1", s[0])
        )
    }

    return render(
        request,
        "series_list.html",
        {"all_series": sorted_series, "series_count": series_books.count()},
    )
