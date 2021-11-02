from itertools import groupby
from typing import Any, Callable

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import generic

from library.models import Author, Book, BookQuerySet, Tag
from library.utils import flatten


class IndexView(LoginRequiredMixin, generic.ListView[Book]):
    categories: list[tuple[str, Callable[[BookQuerySet], BookQuerySet]]]
    template_name = "report.html"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.categories = [
            (
                "Missing ISBN",
                lambda owned_books: owned_books.filter(isbn="")
                .exclude(
                    first_author__surname__in=["Jacobin", "Tribune", "New Left Review"]
                )
                .exclude(edition_format=3, asin__ne="")
                .exclude(edition_published__lt=1965)
                .exclude(first_published__lt=1965, edition_published__isnull=True),
            ),
            (
                "Missing ASIN",
                lambda owned_books: owned_books.filter(
                    edition_format=3, asin=""
                ).exclude(
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
                        "Saqi",
                    ]
                ),
            ),
            (
                "Messy Publisher",
                lambda _: Book.objects.filter(
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
            ("Missing Goodreads", lambda _: Book.objects.filter(goodreads_id="")),
            (
                "Missing Google",
                lambda owned_books: owned_books.filter(google_books_id=""),
            ),
            ("Missing Image", lambda owned_books: owned_books.filter(image_url="")),
            ("Missing Publisher", lambda owned_books: owned_books.filter(publisher="")),
            (
                "Missing Publisher URL",
                lambda owned_books: owned_books.filter(publisher_url="").filter(
                    publisher__in=[
                        "Verso",
                        "Pluto",
                        "Haymarket",
                        "Repeater",
                        "Jacobin Foundation",
                        "Tribune",
                        "Saqi",
                    ]
                ),
            ),
            (
                "Missing Page Count",
                lambda owned_books: owned_books.filter(
                    Q(page_count=0) | Q(page_count__isnull=True)
                ),
            ),
            (
                "Missing Publication Date",
                lambda _: Book.objects.filter(
                    Q(first_published=0) | Q(first_published__isnull=True)
                ),
            ),
            (
                "Ebook edition without ISBN or ASIN",
                lambda owned_books: owned_books.filter(has_ebook_edition=True).filter(
                    ebook_isbn="", ebook_asin=""
                ),
            ),
            (
                "Public domain but no URL",
                lambda _: Book.objects.filter(
                    borrowed_from="public domain", publisher_url=""
                ),
            ),
            (
                "First editions recorded as English for non-English authors",
                lambda _: Book.objects.exclude(
                    language=F("first_author__primary_language")
                ),
            ),
            (
                "Wished for without ASIN",
                lambda _: Book.objects.unowned()
                .filter(want_to_read=True)
                .filter(asin="")
                .exclude(was_borrowed=True),
            ),
            (
                "History without sufficient tags",
                lambda _: Tag.objects["history"].books_uniquely_tagged,
            ),
            (
                "ASIN set for non-ebook",
                lambda owned_books: owned_books.exclude(asin="").exclude(
                    edition_format=3
                ),
            ),
            (
                "ASIN but no alternative ISBN",
                lambda owned_books: owned_books.exclude(asin="").filter(isbn=""),
            ),
        ]

    def get_queryset(self) -> BookQuerySet:
        results = Book.objects.none()

        if page := self.kwargs.get("page"):
            owned_books = Book.objects.owned() | Book.objects.borrowed()
            results = self.categories[int(page) - 1][1](owned_books)

            if order_by := self.request.GET.get("order_by"):
                results = results.order_by(order_by)

        return results

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["categories"] = self.categories
        context["page"] = self.kwargs.get("page")

        if page := self.kwargs.get("page"):
            context["page_title"] = self.categories[int(page) - 1][0]
        else:
            context["page_title"] = "Reports"

        return context


def tags(request: HttpRequest, base_tag: str = "non-fiction") -> HttpResponse:
    excluded_tags = set(
        [
            base_tag,
            "anthology",
            "needs contributors",
            "updated-from-google",
        ]
    )
    if base_tag not in ["fiction", "non-fiction"]:
        excluded_tags |= set(["fiction", "non-fiction"])

    books = Tag.objects[base_tag].books.select_related("first_author")
    toplevel_tags = set(flatten(books.values_list("tags", flat=True))) - excluded_tags

    results = {
        tag: [book for book in books if tag in book.tags] for tag in toplevel_tags
    }

    return render(
        request,
        "report_tag_combinations.html",
        {"results": results, "excluded_tags": excluded_tags},
    )


def related_tags(request: HttpRequest, base_tag: str = "non-fiction") -> HttpResponse:
    excluded_tags = set(
        [
            base_tag,
            "anthology",
            "needs contributors",
            "updated-from-google",
        ]
    )
    if base_tag not in ["fiction", "non-fiction"]:
        excluded_tags |= set(["fiction", "non-fiction"])

    books = Tag.objects[base_tag].books
    toplevel_tags = set(flatten(books.values_list("tags", flat=True))) - excluded_tags

    results = {}
    for tag in toplevel_tags:
        tagged_books = [book for book in books if tag in book.tags]
        related_tags = sorted(flatten([book.tags for book in tagged_books]))
        results[tag] = {
            related_tag: len(list(books))
            for related_tag, books in groupby(related_tags)
        }
        results[tag]["total"] = len(tagged_books)
        results[tag][tag] = len([book for book in tagged_books if len(book.tags) > 2])

    return render(
        request,
        "report_related_tags.html",
        {"results": results, "base_tag": base_tag, "excluded_tags": excluded_tags},
    )


def detached_authors(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "report.html",
        {
            "object_list": Author.objects.exclude(
                first_authored_books__isnull=False
            ).exclude(additional_authored_books__isnull=False),
            "page_title": "Authors without books",
        },
    )
