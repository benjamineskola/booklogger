from random import shuffle

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from library.models import Author, Book, BookAuthor, LogEntry
from library.utils import oxford_comma

import requests
import os
from . import author, book

# Create your views here.


def basic_search(request):
    query = request.GET.get("query")

    results = []
    if query:
        if (
            results := Book.objects.filter(Q(isbn=query) | Q(asin=query))
        ) and results.count() == 1:
            return redirect(results[0])
        results = Book.objects.search(query)

    if results and len(results) == 1:
        return redirect(results[0])

    return render(
        request,
        "search.html",
        {
            "page_title": f"Search{': ' + query if query else ''}",
            "results": results,
            "query": query,
            "goodreads_result": Book.objects.find_on_goodreads(query),
        },
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
    all_tags = {
        "fiction": [book.tags for book in Book.objects.fiction()],
        "non-fiction": [book.tags for book in Book.objects.nonfiction()],
    }

    tags = {
        "untagged": Book.objects.exclude(tags__contains=["non-fiction"])
        .exclude(tags__contains=["fiction"])
        .count(),
        "non-fiction": {
            "no other tags": Book.objects.fiction().filter(tags=["non-fiction"]).count()
        },
        "fiction": {
            "no other tags": Book.objects.nonfiction().filter(tags=["fiction"]).count()
        },
        "all": {},
    }

    for key in ["fiction", "non-fiction"]:
        for book_tags in all_tags[key]:
            for tag in book_tags:
                if tag in tags[key]:
                    tags[key][tag] += 1
                else:
                    tags[key][tag] = 1
                if tag in tags["all"]:
                    tags["all"][tag] += 1
                else:
                    tags["all"][tag] = 1

    for key in ["fiction", "non-fiction", "all"]:
        tags[key] = {
            k: v
            for k, v in sorted(
                tags[key].items(), key=lambda item: item[1], reverse=True
            )
        }

    return render(
        request, "tags/cloud.html", {"page_title": f"All Tags", "tags": tags},
    )


def stats(request):
    books = Book.objects.all()
    owned = books.filter(owned=True)
    read_books = books.filter(want_to_read=False) | books.filter(
        log_entries__isnull=False
    )

    current_year = timezone.now().year
    first_day = timezone.datetime(current_year, 1, 1)
    last_day = timezone.datetime(current_year, 12, 31)
    year_days = (last_day - first_day).days
    current_day = (timezone.datetime.now() - first_day).days
    current_week = (current_day // 7) + 1
    current_year_books = books.filter(log_entries__end_date__year=current_year)
    predicted_books = current_year_books.count() / current_day * year_days
    return render(
        request,
        "stats.html",
        {
            "page_title": f"Library Stats",
            "books": books,
            "owned": owned,
            "read": read_books,
            "current_year": current_year,
            "current_week": current_week,
            "predicted_books": predicted_books,
        },
    )

def import_book(request, query):
    book = Book.objects.create_from_goodreads(query)
    return redirect(book)
