from itertools import groupby

from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import F
from django.db.models.functions import Lower
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader

from library.utils import oxford_comma

from .models import Author, Book, BookAuthor, LogEntry

# Create your views here.


def books_all(request):
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


def owned_books(request):
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


def owned_books_by_date(request):
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


def unowned_books(request):
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


def borrowed_books(request):
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


def reading_books(request):
    currently_reading = LogEntry.objects.filter(end_date__isnull=True).order_by(
        "-progress_date", "start_date"
    )
    currently_reading = filter_logs_by_request(currently_reading, request)
    return render(
        request,
        "logentries/list.html",
        {"page_title": "Read Books", "currently_reading": currently_reading,},
    )


def read_books(request, year=None):
    read = LogEntry.objects.filter(end_date__isnull=False).order_by(
        "end_date", "start_date"
    )
    if year:
        read = read.filter(end_date__year=year)

    read = filter_logs_by_request(read, request)
    return render(
        request, "logentries/list.html", {"page_title": "Read Books", "read": read,},
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


def author_list(request):
    authors = Author.objects.all()

    if gender := request.GET.get("gender"):
        authors = authors.filter(gender=gender)
    if poc := request.GET.get("poc"):
        authors = authors.filter(poc=True)

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
        results = Book.objects.search(query)

    return render(
        request,
        "search.html",
        {"page_title": f"Search{': ' + query if query else ''}", "results": results},
    )


def tag_details(request, tag_name):
    tags = [tag.strip() for tag in tag_name.split(",")]
    books = Book.objects.filter(tags__contains=tags)
    books = filter_books_by_request(books, request)

    paginator = Paginator(books, 100)
    page_number = request.GET.get("page")
    if not page_number:
        page_number = 1
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        "books/list.html",
        {
            "page_title": f"{books.count()} books tagged {oxford_comma(tags)}",
            "page_obj": page_obj,
        },
    )


def tag_cloud(request):
    all_book_tags = [book.tags for book in Book.objects.all()]
    tag_counts = {}
    tag_sizes = {}
    for book_tags in all_book_tags:
        for tag in book_tags:
            if tag in tag_counts:
                tag_counts[tag] += 1
            else:
                tag_counts[tag] = 1

    counts_only = sorted(tag_counts.values())
    median = counts_only[int(len(counts_only) / 2)]
    maxi = counts_only[-1]
    mini = counts_only[0]

    above_median_buckets = (maxi - median) / 100
    below_median_buckets = (median - mini) / 100
    for tag in tag_counts:
        if tag_counts[tag] > median + above_median_buckets:
            tag_sizes[tag] = 1 + (
                ((tag_counts[tag] - median) / above_median_buckets) * 0.02
            )
        elif tag_counts[tag] < median - below_median_buckets:
            tag_sizes[tag] = 1 - (
                ((median - tag_counts[tag]) / below_median_buckets) * 0.02
            )
        else:
            tag_sizes[tag] = 1.0

    return render(
        request, "tags/cloud.html", {"page_title": f"All Tags", "tags": tag_sizes},
    )


def book_add_tags(request, book_id):
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
        return redirect("book_details", book_id=book_id)


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


def stats(request):
    books = Book.objects.all()
    owned = books.filter(owned=True)
    read_books = books.filter(want_to_read=False) | books.filter(
        log_entries__isnull=False
    )
    return render(
        request,
        "stats.html",
        {
            "page_title": f"Library Stats",
            "books": books,
            "owned": owned,
            "read": read_books,
        },
    )
