from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models.functions import Lower
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader

from .models import Author, Book, BookAuthor, LogEntry

# Create your views here.


def index(request):
    return HttpResponse("Hello, world. You're at the library index.")


def books_index(request):
    books = Book.objects.all()
    paginator = Paginator(books, 100)
    page_number = request.GET.get("page")
    if not page_number:
        page_number = 1
    page_obj = paginator.get_page(page_number)
    return render(
        request, "books/list.html", {"page_title": "All Books", "page_obj": page_obj}
    )


def owned_books(request):
    books = Book.objects.filter(owned=True)
    return render(
        request,
        "books/list_by_format.html",
        {"page_title": "Owned Books", "books": books},
    )


def unowned_books(request):
    books = Book.objects.filter(want_to_read=True, owned=False)
    paginator = Paginator(books, 100)
    page_number = request.GET.get("page")
    if not page_number:
        page_number = 1
    page_obj = paginator.get_page(page_number)
    return render(
        request, "books/list.html", {"page_title": "Wishlist", "page_obj": page_obj},
    )


def borrowed_books(request):
    books = Book.objects.filter(was_borrowed=True)
    paginator = Paginator(books, 100)
    page_number = request.GET.get("page")
    if not page_number:
        page_number = 1
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        "books/list.html",
        {"page_title": "Borrowed Books", "page_obj": page_obj},
    )


def author_details(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    return render(
        request, "authors/details.html", {"author": author, "page_title": author}
    )


def book_details(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    return render(
        request,
        "books/details.html",
        {"book": book, "page_title": f"{book.title} by {book.display_authors}"},
    )


def read_books(request):
    currently_reading = LogEntry.objects.filter(end_date__isnull=True).order_by(
        "-progress_date", "start_date"
    )
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
    want_to_read = Book.objects.filter(want_to_read=True, owned=True).order_by(
        "edition_format",
        Lower("first_author__surname"),
        Lower("first_author__forenames"),
        "series",
        "series_order",
        "title",
    )
    paginator = Paginator(want_to_read, 100)
    page_number = request.GET.get("page")
    if not page_number:
        page_number = 1
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "books/toread.html",
        {"page_obj": page_obj, "page_title": "Reading List"},
    )


def all_authors(request):
    authors = Author.objects.all()
    paginator = Paginator(authors, 100)
    page_number = request.GET.get("page")
    if not page_number:
        page_number = 1
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        "authors/list.html",
        {
            "page_obj": page_obj,
            "page_title": "Authors",
            "total_authors": authors.count(),
        },
    )


def start_reading(request, book_id):
    if not request.user.is_authenticated:
        raise PermissionDenied
    if request.method == "POST":
        book = get_object_or_404(Book, pk=book_id)
        book.start_reading()
    return redirect("book_details", book_id=book_id)


def finish_reading(request, book_id):
    if not request.user.is_authenticated:
        raise PermissionDenied
    if request.method == "POST":
        book = get_object_or_404(Book, pk=book_id)
        book.finish_reading()
    return redirect("book_details", book_id=book_id)


def update_progress(request, book_id):
    if not request.user.is_authenticated:
        raise PermissionDenied
    if request.method == "POST":
        book = get_object_or_404(Book, pk=book_id)
        progress = 0
        if request.POST["pages"] and book.page_count:
            progress = int(int(request.POST["pages"]) / book.page_count * 100)
        elif request.POST["percentage"]:
            progress = int(request.POST["percentage"])
        if progress:
            book.update_progress(progress)
    return redirect("book_details", book_id=book_id)


def basic_search(request):
    query = request.GET.get("query")

    results = []
    if query:
        authors = [(a.distance, a) for a in Author.objects.search(query)[0:20]]
        books = [(b.distance, b) for b in Book.objects.search(query)[0:20]]
        results = authors + books
        results.sort(key=lambda x: x[0])

    return render(
        request,
        "search.html",
        {"page_title": f"Search{': ' + query if query else ''}", "results": results},
    )
