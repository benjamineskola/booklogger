from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from library.models import Book


def list(request: HttpRequest) -> HttpResponse:
    publisher_books = Book.objects.exclude(publisher="").filter(
        private__in=([True, False] if request.user.is_authenticated else [False])
    )

    counts = {}
    for book in publisher_books:
        publisher = book.publisher
        if publisher not in counts:
            counts[publisher] = 0

        counts[publisher] += 1

    return render(
        request,
        "publisher_list.html",
        {"publishers": counts, "count": publisher_books.count()},
    )
