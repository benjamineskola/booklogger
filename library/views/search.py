from django.db.models import Q
from django.shortcuts import redirect, render

from library.models import Author, Book


def basic_search(request):
    query = request.GET.get("query")

    authors = []
    books = []
    if query:
        if (
            books := Book.objects.filter(Q(isbn=query) | Q(asin=query))
        ) and books.count() == 1:
            return redirect(books[0])
        books = Book.objects.search(query)
        authors = Author.objects.search(query).filter(similarity__gt=0.25)

    return render(
        request,
        "search.html",
        {
            "page_title": f"Search{': ' + query if query else ''}",
            "authors": authors,
            "books": books,
            "query": query,
        },
    )
