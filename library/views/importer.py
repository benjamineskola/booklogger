import json
import re
from typing import Optional, Union

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from library.models import Author, Book
from library.utils import create, goodreads


@login_required
def import_book(request: HttpRequest, query: Optional[str] = None) -> HttpResponse:
    if request.method == "GET" and not query:
        query = request.GET.get("query")

    if request.method == "POST":
        data = json.loads(request.POST["data"])
        query = request.POST.get("query")

        if query:
            if len(query) == 13 and query.startswith("978"):
                data["isbn"] = query
            elif re.match(r"^B[A-Z0-9]{9}$", query):
                data["asin"] = query
                data["edition_format"] = Book.Format.EBOOK

        book = create.book(data)
        if book:
            return redirect("library:book_edit", slug=book.slug)
        else:
            return redirect("library:book_import", query=query)
    else:
        goodreads_results = []
        matches = {}
        if query and (goodreads_results := goodreads.find_all(query)):
            for result in goodreads_results:
                match = Book.objects.search(
                    f"{result['author']} {result['title']}"
                ).first()
                if match:
                    matches[result["goodreads_id"]] = match

        return render(
            request,
            "import.html",
            {
                "query": query,
                "goodreads_results": goodreads_results,
                "matches": matches,
            },
        )


@login_required
def bulk_import(request: HttpRequest) -> HttpResponse:
    if request.POST:
        data = request.POST["data"]

        results: list[tuple[Union[Author, Book], bool]] = []
        failures = []

        for entry in data.strip("\r\n").split("\n"):
            title, *author_names = entry.strip("\r\n").split(";")

            author_names = [j for i in author_names if (j := i.strip())]

            if not title.strip():
                continue

            try:
                book = create.book(
                    {
                        "title": title.strip(),
                        "authors": author_names,
                    }
                )
                results.append((book, True))
            except Exception as e:
                failures.append((title, author_names, e))
                continue

        return render(
            request,
            "bulk_import.html",
            {
                "page_title": "Import",
                "data": data,
                "results": results,
                "failures": failures,
            },
        )
    else:
        return render(
            request,
            "bulk_import.html",
            {"page_title": "Import"},
        )
