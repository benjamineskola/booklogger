from itertools import groupby

from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import F
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect, render

from library.models import Author, Book, BookAuthor, LogEntry


def all(request):
    books = Book.objects.all()
    books = filter_books_by_request(books, request)

    paginator = Paginator(books, 100)
    page_number = request.GET.get("page")
    if not page_number:
        page_number = 1
    page_obj = paginator.get_page(page_number)
    return render(
        request, "books/list.html", {"page_title": "All Books", "page_obj": page_obj}
    )


def owned(request):
    books = Book.objects.filter(owned=True)
    books = filter_books_by_request(books, request)

    paginator = Paginator(books, 100)
    page_number = request.GET.get("page")
    if not page_number:
        page_number = 1
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "books/list_by_format.html",
        {"page_title": "Owned Books", "page_obj": page_obj},
    )


def owned_by_date(request):
    books = Book.objects.filter(owned=True).order_by(
        F("acquired_date").desc(nulls_last=True)
    )
    books = filter_books_by_request(books, request)

    paginator = Paginator(books, 100)
    page_number = request.GET.get("page")
    if not page_number:
        page_number = 1
    page_obj = paginator.get_page(page_number)

    groups = [
        (d, list(l))
        for d, l in groupby(
            page_obj.object_list, lambda b: b.acquired_date or "Undated"
        )
    ]

    return render(
        request,
        "books/list_by_date.html",
        {"page_title": "Owned Books", "page_obj": page_obj, "page_groups": groups},
    )


def unowned(request):
    books = Book.objects.filter(want_to_read=True, owned=False)
    books = filter_books_by_request(books, request)

    paginator = Paginator(books, 100)
    page_number = request.GET.get("page")
    if not page_number:
        page_number = 1
    page_obj = paginator.get_page(page_number)
    return render(
        request, "books/list.html", {"page_title": "Wishlist", "page_obj": page_obj},
    )


def borrowed(request):
    books = Book.objects.filter(was_borrowed=True)
    books = filter_books_by_request(books, request)

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


def currently_reading(request):
    currently_reading = LogEntry.objects.filter(end_date__isnull=True).order_by(
        "-progress_date", "start_date"
    )
    currently_reading = filter_logs_by_request(currently_reading, request)
    return render(
        request,
        "logentries/list.html",
        {"page_title": "Read Books", "currently_reading": currently_reading,},
    )


def read(request, year=None):
    read = LogEntry.objects.filter(end_date__isnull=False).order_by(
        "end_date", "start_date"
    )
    if year:
        read = read.filter(end_date__year=year)

    read = filter_logs_by_request(read, request)
    return render(
        request, "logentries/list.html", {"page_title": "Read Books", "read": read,},
    )


def unread(request):
    want_to_read = Book.objects.filter(want_to_read=True, owned=True).order_by(
        "edition_format",
        Lower("first_author__surname"),
        Lower("first_author__forenames"),
        "series",
        "series_order",
        "title",
    )

    want_to_read = filter_books_by_request(want_to_read, request)

    paginator = Paginator(want_to_read, 100)
    page_number = request.GET.get("page")
    if not page_number:
        page_number = 1
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "books/toread.html",
        {
            "page_obj": page_obj,
            "page_title": f"Reading List ({want_to_read.count()} books)",
        },
    )


def details(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    return render(
        request,
        "books/details.html",
        {"book": book, "page_title": f"{book.title} by {book.display_authors}"},
    )


def start_reading(request, book_id):
    if not request.user.is_authenticated:
        raise PermissionDenied
    if request.method == "POST":
        book = get_object_or_404(Book, pk=book_id)
        book.start_reading()
    return redirect("library:book_details", book_id=book_id)


def finish_reading(request, book_id):
    if not request.user.is_authenticated:
        raise PermissionDenied
    if request.method == "POST":
        book = get_object_or_404(Book, pk=book_id)
        book.finish_reading()
    return redirect("library:book_details", book_id=book_id)


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
    return redirect("library:book_details", book_id=book_id)


def add_tags(request, book_id):
    if not request.user.is_authenticated:
        raise PermissionDenied
    if request.method == "POST":
        book = get_object_or_404(Book, pk=book_id)
        for tag in request.POST.get("tags").split(","):
            clean_tag = tag.strip()
            if not clean_tag in book.tags:
                book.tags.append(clean_tag)
        book.save()
    if next := request.GET.get("next"):
        return redirect(next)
    else:
        return redirect("library:book_details", book_id=book_id)


def filter_books_by_request(qs, request):
    if gender := request.GET.get("gender"):
        qs = qs.filter(first_author__gender=gender)
    if poc := request.GET.get("poc"):
        qs = qs.filter(first_author__poc=True)
    if tags := request.GET.get("tags"):
        qs = qs.filter(tags__contains=[tag.strip() for tag in tags.split(",")])

    return qs


def filter_logs_by_request(qs, request):
    if gender := request.GET.get("gender"):
        qs = qs.filter(book__first_author__gender=gender)
    if poc := request.GET.get("poc"):
        qs = qs.filter(book__first_author__poc=True)
    if tags := request.GET.get("tags"):
        qs = qs.filter(book__tags__contains=[tag.strip() for tag in tags.split(",")])

    return qs
