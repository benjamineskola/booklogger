from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from library.models import Author, Book, BookAuthor, LogEntry
from library.utils import oxford_comma

from . import book

# Create your views here.


def author_details(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    return render(
        request, "authors/details.html", {"author": author, "page_title": author}
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
    books = book.filter_books_by_request(books, request)

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
