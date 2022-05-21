from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse

from library.models import Book


def index(request: HttpRequest) -> HttpResponse:
    publisher_books = Book.objects.exclude(publisher="").filter(
        private__in=([True, False] if request.user.is_authenticated else [False])
    )

    counts = {}
    for book in publisher_books:
        publisher = book.publisher
        if publisher not in counts:
            counts[publisher] = 0

        counts[publisher] += 1

    return TemplateResponse(
        request,
        "publisher_list.html",
        {"publishers": counts, "count": len(counts.keys())},
    )
