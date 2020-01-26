from django.db.models.functions import Lower
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template import loader

from .models import Author, Book, BookAuthor, LogEntry

# Create your views here.


def index(request):
    return HttpResponse("Hello, world. You're at the library index.")


def books_index(request):
    books = Book.objects.all()
    return render(
        request, "books/list.html", {"page_title": "All Books", "books": books}
    )


def owned_books(request):
    books = Book.objects.filter(owned=True)
    return render(
        request,
        "books/list_by_format.html",
        {"page_title": "Owned Books", "books": books},
    )


def unowned_books(request):
    books = Book.objects.filter(owned=False)
    return render(
        request, "books/list.html", {"page_title": "Unowned Books", "books": books},
    )


def borrowed_books(request):
    books = Book.objects.filter(was_borrowed=True)
    return render(
        request, "books/list.html", {"page_title": "Borrowed Books", "books": books}
    )


def author_details(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    return render(request, "authors/details.html", {"author": author})


def book_details(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    return render(request, "books/details.html", {"book": book})


def read_books(request):
    currently_reading = LogEntry.objects.filter(end_date__isnull=True)
    read = LogEntry.objects.filter(end_date__isnull=False).order_by(
        "end_date", "start_date"
    )
    return render(
        request,
        "logentries/list.html",
        {
            "page_title": "Read Books",
            "read": read,
            "currently_reading": currently_reading,
        },
    )


def unread_books(request):
    want_to_read = Book.objects.filter(want_to_read=True)
    return render(request, "books/toread.html", {"books": want_to_read})


def all_authors(request):
    authors = Author.objects.order_by(Lower("surname"), Lower("forenames"))
    return render(request, "authors/list.html", {"authors": authors})
