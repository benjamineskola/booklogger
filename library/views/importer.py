import csv
import json
import logging
import re
from typing import Any

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils import timezone

from library.models import Book, Queue
from library.utils import create, flatten, goodreads

logger = logging.getLogger(__name__)


@login_required
def import_book(request: HttpRequest, query: str | None = None) -> HttpResponse:
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

    return TemplateResponse(
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
        elif request.POST["input_format"] == "verso":
            for line in lines:
                if not line:
                    continue
                book = _verso_bulk_import(line)
                if not book:
                    continue
                book["edition_format"] = Book.Format.EBOOK
                book["publisher"] = "Verso"
                book["owned"] = True
                queue_item = Queue(data=book)
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

        return TemplateResponse(
            request,
            "bulk_import.html",
            {
                "page_title": "Import",
                "data": data,
            },
        )

    return TemplateResponse(
        request,
        "bulk_import.html",
        {"page_title": "Import"},
    )


def _verso_bulk_import(line: str) -> dict[str, Any] | None:
    title, _, isbn = line.rsplit(", ", 2)
    _, title = title.strip().split(" ", 1)
    title, *author_names = re.split(r" (?:Edited )*?by ", title, 1)
    if author_names:
        authors = flatten(author.split(" and ") for author in author_names)

    try:
        book = Book.objects.get(title__istartswith=title.lower())
        logger.warning("found %s in the database, skipping", title)

        if not book.owned:
            book.isbn = isbn
            book.edition_format = Book.Format.EBOOK
            book.publisher = "Verso"
            book.mark_owned()
            book.save()
        elif book.edition_format != Book.Format.EBOOK and not book.has_ebook_edition:
            # looks like a hard copy is already owned
            book.ebook_isbn = isbn
            book.has_ebook_edition = True
            book.ebook_acquired_date = timezone.now()
            book.save()
        return None  # noqa: TRY300
    except Book.DoesNotExist:
        logger.warning("no book named %s in the database, continuing", title)

    if goodreads_book := goodreads.find(isbn):
        goodreads_book["isbn"] = isbn
        found_title, *_ = goodreads_book["title"].split(": ", 1)
        if found_title.lower() == title.lower():
            logger.info("found %s on goodreads", title)
            return goodreads_book

        logger.warning("got {found_title} instead of %s", title)
    else:
        logger.warning("could not find %s by isbn", title)
        goodreads_book = goodreads.find(f"{title} {' '.join(authors)}")
        if not goodreads_book:
            logger.warning(
                "!!! couldn't find any matches for {title} (%s), creating a new one",
                isbn,
            )
            return {
                "title": title,
                "isbn": isbn,
                "authors": [(author, "") for author in authors],
                "owned": True,
            }

        goodreads_book["isbn"] = isbn
        found_title, *_ = goodreads_book["title"].split(": ", 1)
        if found_title.lower() == title.lower():
            logger.info("found %s on goodreads by name", title)
            return goodreads_book

        logger.warning("got {found_title} instead of %s", title)
        logger.warning("!!! creating {title} (%s)", isbn)
        return {
            "title": title,
            "isbn": isbn,
            "authors": [(author, "") for author in authors],
            "owned": True,
        }
    return None
