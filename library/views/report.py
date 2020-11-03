from django.db.models import F, Q
from django.shortcuts import render

from library.models import Book


def report(request, page=None):
    categories = {}

    categories = [
        (
            "Missing ISBN",
            lambda: owned_books.filter(isbn="")
            .exclude(
                first_author__surname__in=["Jacobin", "Tribune", "New Left Review"]
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
        (
            "History without sufficient tags",
            lambda: Book.objects.filter(
                tags__contains=["history", "non-fiction"]
            ).filter(tags__contained_by=["history", "non-fiction"]),
        ),
    ]

    results = None

    if page:
        owned_books = Book.objects.filter(owned_by__isnull=False)
        results = categories[int(page) - 1][1]()

    if order_by := request.GET.get("order_by"):
        results = results.order_by(order_by)

    return render(
        request,
        "report.html",
        {"categories": categories, "results": results, "page": page},
    )


def tags(request):
    base_tags = ["non-fiction"]
    excluded_tags = set(
        base_tags + ["updated-from-google", "needs contributors", "anthology"]
    )

    books = Book.objects.filter(tags__contains=base_tags).order_by("tags")
    toplevel_tags = set(sum(books.values_list("tags", flat=True), [])) - excluded_tags

    results = {tag: books.filter(tags__contains=[tag]) for tag in toplevel_tags}

    return render(
        request,
        "history_report.html",
        {"results": results, "excluded_tags": excluded_tags},
    )
