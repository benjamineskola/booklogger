import json
import math
import re
from typing import Any

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import generic
from django.views.decorators.http import require_POST

from library.forms import (
    BookAuthorFormSet,
    BookForm,
    LogEntryFormSet,
    ReadingListEntryFormSet,
)
from library.models import Book, BookQuerySet, Tag
from library.utils import oxford_comma


class IndexView(generic.ListView[Book]):
    paginate_by = 100

    filter_by: dict[str, Any] = {}
    sort_by = ""
    reverse_sort = False
    page_title = "All Books"
    show_format_filters = False

    def get_queryset(self) -> BookQuerySet:
        books = (
            Book.objects.select_related("first_author")
            .prefetch_related("additional_authors", "log_entries")
            .filter(
                private__in=(
                    [True, False] if self.request.user.is_authenticated else [False]
                )
            )
        )

        if "filter_by" in self.kwargs:
            self.filter_by = self.kwargs["filter_by"]

        if "show_format_filters" in self.kwargs:
            self.show_format_filters = self.kwargs["show_format_filters"]

        if self.filter_by:
            books = books.filter(**self.filter_by)

        if edition_format := self.kwargs.get("format"):
            books = books.filter_by_format(edition_format)

        if "sort_by" in self.request.GET:
            self.sort_by = self.request.GET["sort_by"]
        elif "sort_by" in self.kwargs:
            self.sort_by = self.kwargs["sort_by"]

        if self.sort_by:
            books = self._sort_by_request(books)

        return books.filter_by_request(self.request).distinct()

    def _sort_by_request(self, books: BookQuerySet) -> BookQuerySet:
        field_names = [f.name for f in Book._meta.get_fields()]  # noqa: SLF001
        field_names.append("read_date")

        if self.sort_by.startswith("-"):
            self.sort_by = self.sort_by[1:]
            self.reverse_sort = True

        if (
            self.sort_by in ["edition_format", "rating", "page_count"]
            or "date" in self.sort_by
            or "published" in self.sort_by
        ):
            self.reverse_sort = not self.reverse_sort

        if self.sort_by in field_names:
            if self.sort_by == "read_date":
                self.sort_by = "log_entries__end_date"

            ordering = Book._meta.ordering or []  # noqa: SLF001

            sort_func = (
                F(self.sort_by).desc(nulls_last=True)
                if self.reverse_sort
                else self.sort_by
            )

            return books.order_by(sort_func, *ordering)

        return books

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["formats"] = Book.Format.choices
        context["format"] = self.kwargs.get("format")
        context["counts"] = {
            f: self.get_queryset().filter(edition_format=f).count()
            for f, _ in context["formats"]
        }
        context["stats"] = {
            "total": self.get_queryset().distinct().count(),
            "owned": self.get_queryset().owned().count(),
            "read": self.get_queryset().read().count(),
        }

        if tags := self.request.GET.get("tags"):
            context["tags"] = [
                Tag.objects.get(name=tag)
                for tag in tags.split(",")
                if tag != "untagged"
            ]

        if "page_title" in self.kwargs:
            self.page_title = self.kwargs["page_title"]
        context["page_title"] = self.page_title + f" ({context['stats']['total']})"
        if self.sort_by:
            context["page_title"] += f" by {re.sub(r'_', ' ', self.sort_by.title())}"

            if (
                self.sort_by in ["edition_format", "rating"]
                or "date" in self.sort_by
                or "published" in self.sort_by
            ):
                context["group_by"] = self.sort_by
                context["reverse_sort"] = self.reverse_sort

        context["show_format_filters"] = self.show_format_filters

        return context


class OwnedIndexView(IndexView):
    page_title = "Owned Books"
    show_format_filters = True

    def get_queryset(self) -> BookQuerySet:
        books = super().get_queryset()
        return books.owned()


class BorrowedIndexView(IndexView):
    page_title = "Borrowed Books"
    show_format_filters = True

    def get_queryset(self) -> BookQuerySet:
        books = super().get_queryset()
        return books.borrowed() | books.owned_by("sara")


class UnreadIndexView(IndexView):
    filter_by = {"want_to_read": True}
    page_title = "To-Read Books"
    show_format_filters = True

    def get_queryset(self) -> BookQuerySet:
        books = super().get_queryset()
        return (
            books.available() | books.filter(edition_format=Book.Format["WEB"])
        ).exclude(tags__name="reference")


class SeriesIndexView(IndexView):
    sort_by = "series_order"

    def get_queryset(self) -> BookQuerySet:
        books = super().get_queryset()
        self.series = self.kwargs["series"].replace("%2f", "/")
        return books.filter(series=self.series)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context[
            "page_title"
        ] = f"{self.series} Series ({len(context['page_obj'])} books)"
        return context


class PublisherIndexView(IndexView):
    def get_queryset(self) -> BookQuerySet:
        books = super().get_queryset()
        self.publisher = self.kwargs["publisher"].replace("%2f", "/")
        return books.filter(publisher=self.publisher)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context[
            "page_title"
        ] = f"Books published by {self.publisher} ({self.get_queryset().count()} books)"
        return context


class TagIndexView(IndexView):
    def get_queryset(self) -> BookQuerySet:
        books = super().get_queryset()
        tags: list[str] = [tag.strip() for tag in self.kwargs["tag_name"].split(",")]

        if tags == ["untagged"]:
            return books.filter(tags__isnull=True)
        if len(tags) == 1 and tags[0].endswith("!"):
            tag = get_object_or_404(Tag, name=tags[0][0:-1])
            return tag.books_uniquely_tagged
        for tag_name in tags:
            books &= Tag.objects.get(name=tag_name).books_recursive
        return books

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["tags"] = [
            Tag.objects.get(name=tag.strip("!"))
            for tag in self.kwargs["tag_name"].split(",")
            if tag != "untagged"
        ]
        context[
            "page_title"
        ] = f"{self.get_queryset().count()} books tagged {'only ' if '!' in self.kwargs['tag_name'] else ''}{oxford_comma([t.name for t in context['tags']])}"
        return context


class ReviewedView(IndexView):
    page_title = "Reviewed Books"

    def get_queryset(self) -> BookQuerySet:
        return super().get_queryset().exclude(review="")


class UnreviewedView(IndexView):
    page_title = "Unreviewed Books"

    def get_queryset(self) -> BookQuerySet:
        return super().get_queryset().filter(review="").read()


class DetailView(generic.DetailView[Book]):
    model = Book

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        context["page_title"] = book.display_title + " by " + str(book.first_author)
        return context

    def dispatch(self, *args: Any, **kwargs: Any) -> Any:
        obj = self.get_object()
        if obj.private and not self.request.user.is_authenticated:
            return HttpResponseNotFound("Page not found")

        return super().dispatch(*args, **kwargs)


@login_required
@require_POST
def start_reading(_request: HttpRequest, slug: str) -> HttpResponse:
    book = get_object_or_404(Book, slug=slug)
    book.start_reading()
    return redirect("library:book_details", slug=slug)


@login_required
@require_POST
def finish_reading(_request: HttpRequest, slug: str) -> HttpResponse:
    book = get_object_or_404(Book, slug=slug)
    book.finish_reading()
    return redirect("library:book_details", slug=slug)


@login_required
@require_POST
def update_progress(request: HttpRequest, slug: str) -> HttpResponse:
    book = get_object_or_404(Book, slug=slug)

    if request.POST["progress_type"] == "pages":
        page = int(request.POST["value"])
        percentage = 0.0
    else:
        page = 0
        percentage = float(request.POST["value"])

    percentage = book.update_progress(percentage=percentage, page=page)

    if page and book.page_count:
        progress_text = f"on page {page} of {book.page_count} ({percentage:.4g}% done)"
    else:
        progress_text = f"{percentage:.4g}% done"
    progress_text += f" on {timezone.now().strftime('%d %B, %Y')}"

    return HttpResponse(
        json.dumps({"percentage": percentage, "progress_text": progress_text})
    )


@login_required
@require_POST
def add_tags(request: HttpRequest, slug: str) -> HttpResponse:
    book = get_object_or_404(Book, slug=slug)
    tags = request.POST.get("tags", "").split(",")

    if tags:
        start_tags = [tag.name for tag in book.tags.all()]
        for tag in tags:
            book.tags.add(Tag.objects.get(name=tag))
        book.save()
        tags = sorted({tag.name for tag in book.tags.all()}.difference(start_tags))

    return HttpResponse(json.dumps({"tags": tags}))


@login_required
@require_POST
def remove_tags(request: HttpRequest, slug: str) -> HttpResponse:
    book = get_object_or_404(Book, slug=slug)
    tags = request.POST.get("tags", "").split(",")
    for tag_name in tags:
        tag = Tag.objects.get(name=tag_name)
        book.tags.remove(tag)
        if not tag.books.count() and not tag.children.count():
            tag.delete()
    book.save()

    return redirect("library:book_details", slug=slug)


@login_required
@require_POST
def mark_owned(_request: HttpRequest, slug: str) -> HttpResponse:
    book = get_object_or_404(Book, slug=slug)

    if not book.edition_format:
        edit_url = reverse("library:book_edit", kwargs={"slug": slug})
        return redirect(edit_url + "?mark_owned=true")

    book.mark_owned()
    return redirect("library:book_details", slug=slug)


@login_required
@require_POST
def mark_read_sometime(_request: HttpRequest, slug: str) -> HttpResponse:
    book = get_object_or_404(Book, slug=slug)
    book.mark_read_sometime()
    return redirect("library:book_details", slug=slug)


@login_required
@require_POST
def rate(request: HttpRequest, slug: str) -> HttpResponse:
    book = get_object_or_404(Book, slug=slug)
    if rating := request.POST["rating"]:
        book.rating = rating
        book.save()

    return redirect("library:book_details", slug=slug)


class BookEditMixin(
    generic.edit.ModelFormMixin[Book, BookForm], generic.edit.ProcessFormView
):
    form_class = BookForm
    model = Book

    def form_valid(self, form: BookForm) -> HttpResponse:
        context = self.get_context_data()
        self.object = form.save()

        response: HttpResponse
        if all(formset.is_valid() for formset in context["inline_formsets"]):
            for formset in context["inline_formsets"]:
                formset.instance = self.object
                formset.save()

                for subform in formset:
                    if (
                        formset.data.get(subform.prefix + "-DELETE") == "on"
                        and subform.instance.id
                    ):
                        subform.instance.delete()

            response = super().form_valid(form)
        else:
            response = super().form_invalid(form)

        if "mark_owned" in self.request.GET:
            self.object.mark_owned()

        return response

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["inline_formsets"] = [
                BookAuthorFormSet(self.request.POST, instance=self.object),
                LogEntryFormSet(self.request.POST, instance=self.object),
                ReadingListEntryFormSet(self.request.POST, instance=self.object),
            ]
        else:
            context["inline_formsets"] = [
                BookAuthorFormSet(instance=self.object),
                LogEntryFormSet(instance=self.object),
                ReadingListEntryFormSet(instance=self.object),
            ]

        context["page_title"] = f"Editing {self.object}" if self.object else "New book"

        return context


class NewView(  # type: ignore[misc]
    LoginRequiredMixin, generic.edit.CreateView[Book, BookForm], BookEditMixin
):
    pass


class EditView(  # type: ignore[misc]
    LoginRequiredMixin, generic.edit.UpdateView[Book, BookForm], BookEditMixin
):
    pass


class DeleteView(LoginRequiredMixin, generic.edit.DeleteView[Book, BookForm]):
    model = Book
    object: Book  # noqa: A003
    success_url = reverse_lazy("library:books_all")
    template_name = "confirm_delete.html"


def export_books(request: HttpRequest) -> JsonResponse:
    page = int(request.GET.get("page", 1))
    count = 100
    start = (page - 1) * 100
    books = Book.objects.all()[start : start + count]
    result = {
        "page": page,
        "per_page": count,
        "total": Book.objects.count(),
        "total_pages": math.ceil(Book.objects.count() / count),
        "this_page": books.count(),
        "books": [book.to_json() for book in books],
    }

    return JsonResponse(result)
