from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from library.models import Author, Book


def basic_search(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("query")

    authors = Author.objects.none()
    books = Book.objects.none()
    if query:
        if (
            books := Book.objects.filter(Q(isbn=query) | Q(asin=query))
        ) and books.count() == 1:
            return redirect(books[0])
        books = Book.objects.search(query).filter(
            private__in=([True, False] if request.user.is_authenticated else [False])
        )
        authors = Author.objects.search(query)

    return TemplateResponse(
        request,
        "search.html",
        {
            "page_title": f"Search{': ' + query if query else ''}",
            "authors": authors,
            "books": books,
            "query": query,
        },
    )
