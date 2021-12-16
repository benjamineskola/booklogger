import csv
import json
import re
from typing import Optional

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from library.models import Book, Queue
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

        book, *_ = create.book(data)
        if book:
            return redirect("library:book_edit", slug=book.slug)
        return redirect("library:book_import", query=query)

    goodreads_results = []
    matches = {}
    if query and (goodreads_results := goodreads.find_all(query)):
        for result in goodreads_results:
            match = Book.objects.search(
                f"{result['authors'][0][0]} {result['title']}"
            ).first()
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
        data = str(request.POST["data"])
        lines = [line.strip() for line in data.split("\n")]

        if request.POST["input_format"] == "csv":
            reader = csv.DictReader(
                lines[1:], fieldnames=[n.lower() for n in lines[0].split(",")]
            )
            for entry in reader:
                queue_item = Queue(
                    data={
                        "title": entry["title"].strip().split(":")[0],
                        "authors": [(entry["author"], "")]
                        + (
                            [
                                (author, "")
                                for author in entry["additional authors"].split(", ")
                            ]
                            if "additional authors" in entry
                            and entry["additional authors"]
                            else []
                        ),
                        # goodreads
                        "first_published": entry["original publication year"]
                        if "original publication year" in entry
                        and entry["original publication year"].isnumeric()
                        else 0,
                        "isbn": entry["isbn13"].strip('="')
                        if "isbn13" in entry
                        else "",
                        "page_count": entry["number of pages"]
                        if "number of pages" in entry
                        and entry["number of pages"].isnumeric()
                        else 0,
                        "want_to_read": entry["exclusive shelf"] != "read"
                        if "exclusive shelf" in entry
                        else True,
                        "goodreads_id": entry["book id"] if "book id" in entry else "",
                        # ereaderiq
                        "asin": entry["asin"] if "asin" in entry else "",
                        "image_url": entry["image url"] if "image url" in entry else "",
                        "publisher": entry["publisher"] if "publisher" in entry else "",
                    }
                )
                queue_item.save()
        else:
            for line in lines:
                title, *author_names = line.strip("\r\n").split(";")

                authors = [
                    (j[0].strip(), j[1].strip() if len(j) > 1 else "")
                    for i in author_names
                    if (j := i.strip().split(":"))
                ]

                if not title.strip():
                    continue

                queue_item = Queue(data={"title": title.strip, "authors": authors})
                queue_item.save()

        return render(
            request,
            "bulk_import.html",
            {
                "page_title": "Import",
                "data": data,
            },
        )

    return render(
        request,
        "bulk_import.html",
        {"page_title": "Import"},
    )
