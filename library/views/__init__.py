from random import shuffle

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from library.models import Author, Book, BookAuthor, LogEntry
from library.utils import oxford_comma

from . import author, book

# Create your views here.


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
    if tags == ["untagged"]:
        condition = {"tags__len": 0}
    else:
        condition = {"tags__contains": tags}
    books = (
        Book.objects.select_related("first_author")
        .prefetch_related("additional_authors", "log_entries")
        .filter(**condition)
        .filter_by_request(request)
    )

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
    tag_counts = {"untagged": 0}
    tag_sizes = {}
    for book_tags in all_book_tags:
        if book_tags:
            for tag in book_tags:
                if tag in tag_counts:
                    tag_counts[tag] += 1
                else:
                    tag_counts[tag] = 1
        else:
            tag_counts["untagged"] += 1

    counts_only = sorted(tag_counts.values())
    median = counts_only[int(len(counts_only) / 2)]
    maxi = max(counts_only)
    mini = min(counts_only)

    above_median_buckets = max(1, int((maxi - median) / 30))
    below_median_buckets = max(1, int((median - mini) / 30))

    tag_sizes = {}

    for i, j in enumerate(range(median, maxi, above_median_buckets)):
        tag_sizes.update(dict([(k[0], i) for k in tag_counts.items() if k[1] >= j]))

    for i, j in enumerate(reversed(range(mini, median, below_median_buckets))):
        tag_sizes.update(dict([(k[0], -i) for k in tag_counts.items() if k[1] <= j]))

    tags = list(tag_sizes.items())
    shuffle(tags)

    return render(
        request, "tags/cloud.html", {"page_title": f"All Tags", "tags": tags},
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
