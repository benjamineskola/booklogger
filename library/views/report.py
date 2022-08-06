from itertools import groupby
from typing import Any, Callable

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.views import generic

from library.models import Author, Book, BookQuerySet, Tag
from library.utils import flatten

ebook_publishers = {
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
}


class IndexView(LoginRequiredMixin, generic.ListView[Book]):
    categories: list[tuple[str, Callable[[], BookQuerySet]]]
    template_name = "report.html"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.categories = [
            (
                "Missing ISBN",
                lambda: Book.objects.owned_by_any()
                .filter(isbn="")
                .exclude(
                    Q(owned_by__isnull=True, parent_edition__owned_by__isnull=False)
                    | Q(
                        owned_by__isnull=True,
                        parent_edition__parent_edition__owned_by__isnull=False,
                    )
                )
                .exclude(
                    first_author__surname__in=["Jacobin", "Tribune", "New Left Review"]
                )
                .exclude(edition_format=3, asin__ne="")
                .exclude(edition_published__lt=1965, edition_published__gt=0)
                .exclude(
                    first_published__lt=1965, first_published__gt=0, edition_published=0
                ),
            ),
            (
                "Missing ASIN",
                lambda: Book.objects.owned_by_any()
                .filter(edition_format=3, asin="")
                .exclude(publisher__in=ebook_publishers),
            ),
            (
                "Messy Publisher",
                lambda: Book.objects.filter(
                    Q(publisher__endswith="Books")
                    | Q(publisher__contains="Company")
                    | Q(publisher__contains="Ltd")
                    | Q(publisher__contains="Limited")
                    | (
                        Q(publisher__contains="Press")
                        & ~Q(publisher="Foreign Languages Press")
                        & ~Q(publisher="Free Press")
                        & ~Q(publisher="History Press")
                        & ~Q(publisher="MIT Press")
                        & ~Q(publisher="New Press")
                        & ~Q(publisher="Polperro Heritage Press")
                        & ~Q(publisher__contains="University")
                    )
                    | (
                        Q(publisher__endswith="Publishers")
                        & ~Q(publisher="International Publishers")
                    )
                    | Q(publisher__endswith="Publishing")
                    | Q(publisher__endswith="Publications")
                    | Q(publisher__startswith="The ")
                    | Q(publisher__contains="Univ.")
                ),
            ),
            ("Missing Goodreads", lambda: Book.objects.filter(goodreads_id="")),
            (
                "Missing Google",
                lambda: Book.objects.filter(google_books_id=""),
            ),
            ("Missing Image", lambda: Book.objects.owned_by_any().filter(image_url="")),
            (
                "Missing Publisher",
                lambda: Book.objects.owned_by_any().filter(publisher=""),
            ),
            (
                "Missing Publisher URL",
                lambda: Book.objects.owned_by_any()
                .filter(publisher_url="")
                .filter(
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
                lambda: Book.objects.owned_by_any().filter(page_count=0),
            ),
            (
                "Missing Publication Date",
                lambda: Book.objects.filter(first_published=0),
            ),
            (
                "Ebook edition without ISBN or ASIN",
                lambda: Book.objects.owned_by_any()
                .filter(has_ebook_edition=True)
                .filter(ebook_isbn="", ebook_asin=""),
            ),
            (
                "Public domain but no URL",
                lambda: Book.objects.filter(
                    borrowed_from="public domain", publisher_url=""
                ),
            ),
            (
                "First editions recorded as English for non-English authors",
                lambda: Book.objects.exclude(
                    language=F("first_author__primary_language")
                ),
            ),
            (
                "Wished for without ASIN",
                lambda: Book.objects.unowned()
                .filter(want_to_read=True)
                .filter(asin="")
                .exclude(was_borrowed=True)
                .exclude(owned_by__isnull=False)
                .exclude(publisher__in=ebook_publishers),
            ),
            (
                "History without sufficient tags",
                lambda: Tag.objects["history"].books_uniquely_tagged,
            ),
            (
                "ASIN set for non-ebook",
                lambda: Book.objects.owned_by_any()
                .exclude(asin="")
                .exclude(edition_format=3),
            ),
            (
                "ASIN but no alternative ISBN",
                lambda: Book.objects.exclude(asin="").filter(isbn=""),
            ),
            (
                "ASIN set for inappropriate publisher",
                lambda: Book.objects.owned_by_any()
                .exclude(asin="")
                .filter(publisher__in=ebook_publishers),
            ),
            (
                "Failed import or otherwise invalid",
                lambda: Book.objects.filter(
                    Q(title="")
                    | Q(title__isnull=True)
                    | Q(slug="")
                    | Q(slug__isnull=True)
                    | Q(first_author__isnull=True)
                ),
            ),
        ]

    def get_queryset(self) -> BookQuerySet:
        results = Book.objects.none()

        if page := self.kwargs.get("page"):
            results = self.categories[int(page) - 1][1]()

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
    excluded_tags = {base_tag, "anthology", "needs contributors", "updated-from-google"}

    if base_tag not in ["fiction", "non-fiction"]:
        excluded_tags |= {"fiction", "non-fiction"}

    toplevel_tags = Tag.objects.exclude(books__isnull=True)

    results = {tag.name: tag.books.all() for tag in toplevel_tags}

    return TemplateResponse(
        request,
        "report_tag_combinations.html",
        {"results": results, "excluded_tags": excluded_tags},
    )


def related_tags(request: HttpRequest, base_tag: str = "non-fiction") -> HttpResponse:
    excluded_tags = {base_tag, "anthology", "needs contributors", "updated-from-google"}

    if base_tag not in ["fiction", "non-fiction"]:
        excluded_tags |= {"fiction", "non-fiction"}

    toplevel_tags = Tag.objects.exclude(books__isnull=True)

    results = {}
    for tag in toplevel_tags:
        tagged_books = tag.books.all()
        related = sorted(flatten([book.tags.all() for book in tagged_books]))
        results[tag.name] = {
            related_tag.name: len(list(books))
            for related_tag, books in groupby(related)
        }
        results[tag.name]["total"] = tagged_books.count()
        results[tag.name][tag.name] = len(
            [book for book in tagged_books if book.tags.count() > 2]
        )

    return TemplateResponse(
        request,
        "report_related_tags.html",
        {"results": results, "base_tag": base_tag, "excluded_tags": excluded_tags},
    )


def detached_authors(request: HttpRequest) -> HttpResponse:
    return TemplateResponse(
        request,
        "report.html",
        {
            "object_list": Author.objects.exclude(
                first_authored_books__isnull=False
            ).exclude(additional_authored_books__isnull=False),
            "page_title": "Authors without books",
        },
    )
