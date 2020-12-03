from django.shortcuts import render

from library.models import Book


def list(request):
    publisher_books = Book.objects.exclude(publisher="")
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
