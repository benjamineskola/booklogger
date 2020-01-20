from django.db.models.functions import Lower
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template import loader

from .models import Author, Book, BookAuthor

# Create your views here.


def index(request):
    return HttpResponse("Hello, world. You're at the library index.")


def books_index(request):
    books = Book.objects.order_by(
        Lower("authors__surname"),
        Lower("authors__forenames"),
        "series",
        "series_order",
        "title",
    )
    return render(request, "books/index.html", {"books": books})


def owned_books(request):
    books = Book.objects.filter(owned=True).order_by(
        Lower("authors__surname"),
        Lower("authors__forenames"),
        "series",
        "series_order",
        "title",
    )
    return render(request, "books/index.html", {"books": books})


def unowned_books(request):
    books = Book.objects.filter(owned=False).order_by(
        Lower("authors__surname"),
        Lower("authors__forenames"),
        "series",
        "series_order",
        "title",
    )
    return render(request, "books/index.html", {"books": books})


def author_details(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    return render(request, "authors/details.html", {"author": author})


def book_details(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    return render(request, "books/details.html", {"book": book})
