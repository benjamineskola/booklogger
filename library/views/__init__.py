import json
import re

from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Q
from django.shortcuts import redirect, render
from django.utils import timezone

from library.models import Author, Book, LogEntry

from . import author, book  # noqa: F401

# Create your views here.


def basic_search(request):
    query = request.GET.get("query")

    books = []
    if query:
        if (
            books := Book.objects.filter(Q(isbn=query) | Q(asin=query))
        ) and books.count() == 1:
            return redirect(results[0])
        books = Book.objects.search(query)
        authors = Author.objects.search(query).filter(similarity__gt=0.25)

    return render(
        request,
        "search.html",
        {
            "page_title": f"Search{': ' + query if query else ''}",
            "authors": authors,
            "books": books,
            "query": query,
        },
    )


def tag_cloud(request):
    all_tags = {
        "fiction": Book.objects.fiction().values_list("tags", flat=True),
        "non-fiction": Book.objects.nonfiction().values_list("tags", flat=True),
    }

    tags = {
        "untagged": Book.objects.exclude(tags__contains=["non-fiction"])
        .exclude(tags__contains=["fiction"])
        .count(),
        "non-fiction": {
            "no other tags": Book.objects.filter(tags=["non-fiction"]).count()
        },
        "fiction": {"no other tags": Book.objects.filter(tags=["fiction"]).count()},
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

    tags_by_name = {}
    tags_by_size = {}
    sorted_tags = {"name": {}, "size": {}}
    for key in ["fiction", "non-fiction", "all"]:
        sorted_tags["name"][key] = {
            k: v for k, v in sorted(tags[key].items(), key=lambda item: item[0])
        }
    for key in ["fiction", "non-fiction", "all"]:
        sorted_tags["size"][key] = {
            k: v
            for k, v in sorted(
                tags[key].items(), key=lambda item: item[1], reverse=True
            )
        }

    return render(
        request, "tags/cloud.html", {"page_title": f"Tags", "tags": sorted_tags,},
    )


def _stats_for_queryset(books):
    fiction = books.fiction()
    nonfiction = books.nonfiction()
    result = {
        "count": books.count(),
        "men": books.by_men().count(),
        "women": books.by_women().count(),
        "both": books.by_women().by_men().count(),
        "neither": books.exclude(first_author__gender=1)
        .exclude(first_author__gender=2)
        .count(),
        "fiction": fiction.count(),
        "nonfiction": nonfiction.count(),
        "breakdowns": {},
    }
    for gender, i in [("men", 1), ("women", 2)]:
        gender_fiction = fiction.by_gender(i)
        gender_nonfiction = nonfiction.by_gender(i)

        result["breakdowns"][gender] = {
            "fiction_count": gender_fiction.count(),
            "percentage_fiction": gender_fiction.count() / max(1, result[gender]) * 100,
            "nonfiction_count": gender_nonfiction.count(),
            "percentage_nonfiction": gender_nonfiction.count()
            / max(1, result[gender])
            * 100,
        }
    for genre in ["fiction", "non-fiction"]:
        genre_books = books.filter(tags__contains=[genre])
        result["breakdowns"][genre] = {
            "men_count": genre_books.by_men().count(),
            "women_count": genre_books.by_women().count(),
            f"percentage_men": genre_books.by_men().count()
            / max(1, genre_books.count())
            * 100,
            f"percentage_women": genre_books.by_women().count()
            / max(1, genre_books.count())
            * 100,
        }
    return result


def stats(request):
    books = Book.objects.all()
    owned = books.filter(owned_by__username="ben")
    owned_count = owned.count()
    read_books = books.read()
    owned_read = owned.read().count()
    want_to_read = owned.filter(want_to_read=True)
    want_to_read_count = want_to_read.count()
    reread = owned.read().filter(want_to_read=True).count()

    books_by_year = {}  # {"all": {"books": books, "count": books.count()}}

    for year in (
        LogEntry.objects.exclude(end_date__isnull=True)
        .distinct("end_date__year")
        .values_list("end_date__year", flat=True)
    ):
        books_by_year[str(year)] = _stats_for_queryset(
            books.filter(log_entries__end_date__year=year)
        )

        books_by_year[str(year)]["acquired"] = books.filter(
            acquired_date__year=year
        ).count()

    books_by_year["total"] = _stats_for_queryset(read_books)

    current_year = timezone.now().year
    first_day = timezone.datetime(current_year, 1, 1)
    last_day = timezone.datetime(current_year, 12, 31)
    year_days = (last_day - first_day).days
    current_day = (timezone.datetime.now() - first_day).days
    current_week = (current_day // 7) + 1
    current_year_count = books.filter(log_entries__end_date__year=current_year).count()
    predicted_count = current_year_count / current_day * year_days

    return render(
        request,
        "stats.html",
        {
            "page_title": f"Library Stats",
            "owned": owned_count,
            "owned_read": owned_read,
            "owned_read_pct": owned_read / owned_count * 100,
            "want_to_read": want_to_read_count,
            "want_to_read_pct": want_to_read_count / owned_count * 100,
            "reread": reread,
            "reread_pct": reread / read_books.count() * 100,
            "current_year": current_year,
            "current_week": current_week,
            "predicted_count": predicted_count,
            "books_by_year": books_by_year,
        },
    )


@login_required
def import_book(request, query=None):
    if request.method == "GET" and not query:
        query = request.GET.get("query")

    if request.method == "POST":
        data = json.loads(request.POST["data"])
        query = request.POST.get("query")
        book = Book.objects.create_from_goodreads(data=data, query=query)
        return redirect("library:book_edit", slug=book.slug)
    else:
        goodreads_results = None
        matches = {}
        if query:
            goodreads_results = Book.objects.find_on_goodreads(query)

            for result in goodreads_results:
                match = Book.objects.search(
                    f"{result['best_book']['author']['name']} {result['best_book']['title']}"
                ).first()
                if match:
                    matches[result["id"]["#text"]] = match

        return render(
            request,
            "books/import.html",
            {
                "query": query,
                "goodreads_results": goodreads_results,
                "matches": matches,
            },
        )


def report(request, page=None):
    categories = {}

    categories = [
        (
            "Missing ISBN",
            lambda: owned_books.filter(isbn="")
            .exclude(
                first_author__surname__in=["Jacobin", "Tribune", "New Left Review",]
            )
            .exclude(edition_format=3, asin__length__gt=0)
            .exclude(edition_published__lt=1965)
            .exclude(first_published__lt=1965, edition_published__isnull=True),
        ),
        (
            "Missing ASIN",
            lambda: owned_books.filter(edition_format=3, asin="").exclude(
                publisher__in=[
                    "Verso",
                    "Pluto",
                    "Haymarket",
                    "Repeater",
                    "New Socialist",
                    "Jacobin Foundation",
                    "Tribune",
                    "No Starch Press",
                    "Pragmatic Bookshelf",
                    "iTunes",
                ]
            ),
        ),
        (
            "Messy Publisher",
            lambda: Book.objects.filter(
                Q(publisher__endswith="Books")
                | Q(publisher__contains="Company")
                | Q(publisher__contains="Ltd")
                | Q(publisher__contains="Limited")
                | Q(publisher__startswith="Bantam ")
                | Q(publisher__startswith="Bloomsbury ")
                | Q(publisher__startswith="Doubleday ")
                | Q(publisher__startswith="Faber ")
                | Q(publisher__startswith="Harper")
                | Q(publisher__startswith="Pan ")
                | Q(publisher__startswith="Penguin ")
                | Q(publisher__startswith="Simon & Schuster ")
                | Q(publisher__startswith="Vintage ")
            ).exclude(
                Q(publisher__contains="University")
                | Q(publisher="Faber & Faber")
                | Q(publisher="HarperCollins")
                | Q(publisher="Pan Macmillan")
            ),
        ),
        ("Missing Goodreads", lambda: Book.objects.filter(goodreads_id="")),
        ("Missing Google", lambda: owned_books.filter(google_books_id="")),
        ("Missing Image", lambda: owned_books.filter(image_url="")),
        ("Missing Publisher", lambda: owned_books.filter(publisher="")),
        (
            "Missing Publisher URL",
            lambda: owned_books.filter(publisher_url="").filter(
                publisher__in=[
                    "Verso",
                    "Pluto",
                    "Haymarket",
                    "Repeater",
                    "Jacobin Foundation",
                    "Tribune",
                ]
            ),
        ),
        (
            "Missing Page Count",
            lambda: owned_books.filter(Q(page_count=0) | Q(page_count__isnull=True)),
        ),
        (
            "Missing Publication Date",
            lambda: Book.objects.filter(
                Q(first_published=0) | Q(first_published__isnull=True)
            ),
        ),
        (
            "Ebook edition without ISBN or ASIN",
            lambda: owned_books.filter(has_ebook_edition=True).filter(
                ebook_isbn="", ebook_asin=""
            ),
        ),
        (
            "Public domain but no URL",
            lambda: Book.objects.filter(
                borrowed_from="public domain", publisher_url=""
            ),
        ),
        (
            "First editions recorded as English for non-English authors",
            lambda: Book.objects.exclude(language=F("first_author__primary_language")),
        ),
        (
            "Wished for without ASIN",
            lambda: Book.objects.filter(owned_by__isnull=True)
            .filter(want_to_read=True)
            .filter(asin="")
            .exclude(was_borrowed=True),
        ),
    ]

    results = None

    if page:
        owned_books = Book.objects.filter(owned_by__isnull=False)
        results = categories[page - 1][1]()

    if order_by := request.GET.get("order_by"):
        results = results.order_by(order_by)

    return render(
        request,
        "books/report.html",
        {"categories": categories, "results": results, "page": page},
    )


def series_list(request):
    all_series = (
        Book.objects.exclude(series="")
        .values_list("series")
        .annotate(count=Count("series"))
        .order_by("series")
    )
    series_count = all_series.count()
    sorted_series = sorted(
        all_series, key=lambda s: re.sub(r"^(A|The) (.*)", r"\2, \1", s[0])
    )

    return render(
        request,
        "books/series_index.html",
        {"all_series": sorted_series, "series_count": series_count},
    )


@login_required
def bulk_import(request):
    if request.POST:
        data = request.POST["data"]

        results = []

        for entry in data.strip("\r\n").split("\n"):
            title, *author_names = entry.strip("\r\n").split(";")

            book, book_created = Book.objects.get_or_create(title__iexact=title.strip())
            if book_created:
                book.title = title.strip()

            first_author_name = author_names.pop(0).strip()
            first_author_role = ""
            if ":" in first_author_name:
                first_author_name, first_author_role = first_author_name.split(":", 1)

            (first_author, fa_created,) = Author.objects.get_or_create_by_single_name(
                first_author_name
            )
            book.first_author = first_author
            book.first_author_role = first_author_role
            book.save()

            results.append((first_author, fa_created))

            for order, name in enumerate(author_names, start=1):
                role = ""
                if ":" in name:
                    name, role = name.split(":", 1)

                author, created = Author.objects.get_or_create_by_single_name(
                    name.strip()
                )
                if author not in book.additional_authors.all():
                    book.add_author(author, order=order, role=role)

                results.append((author, created))

            results.append((book, book_created))

        return render(
            request,
            "bulk_import.html",
            {"page_title": "Import", "data": data, "results": results},
        )
    else:
        return render(request, "bulk_import.html", {"page_title": "Import"},)
