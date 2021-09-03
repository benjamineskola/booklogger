import json
import re
from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic
from django.views.decorators.http import require_POST

from library.forms import (
    BookAuthorFormSet,
    BookForm,
    LogEntryFormSet,
    ReadingListEntryFormSet,
)
from library.models import Book, BookQuerySet, LogEntry, LogEntryQuerySet, Tag
from library.utils import oxford_comma


class IndexView(LoginRequiredMixin, generic.ListView):
    paginate_by = 100

    filter_by = {}
    sort_by = None
    reverse_sort = False
    page_title = "All Books"
    show_format_filters = False

    def get_queryset(self) -> BookQuerySet:
        books = (
            Book.objects.select_related("first_author")
            .prefetch_related("additional_authors", "log_entries")
            .all()
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
            field_names = [f.name for f in Book._meta.get_fields()]
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

                if self.reverse_sort:
                    books = books.order_by(
                        F(self.sort_by).desc(nulls_last=True), *Book._meta.ordering
                    )
                else:
                    books = books.order_by(self.sort_by, *Book._meta.ordering)

        return books.filter_by_request(self.request).distinct()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["formats"] = Book.Format.choices
        context["format"] = self.kwargs.get("format")
        context["counts"] = {
            f: self.get_queryset().filter(edition_format=f).count()
            for f, _ in context["formats"]
        }
        context["stats"] = {
            "total": self.get_queryset().distinct().count(),
            "owned": self.get_queryset().filter(owned_by__isnull=False).count(),
            "read": self.get_queryset().read().count(),
        }

        if tags := self.request.GET.get("tags"):
            context["tags"] = [
                Tag.objects[tag] for tag in tags.split(",") if tag != "untagged"
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
    filter_by = {"owned_by__username": "ben"}
    page_title = "Owned Books"
    show_format_filters = True


class BorrowedIndexView(IndexView):
    page_title = "Borrowed Books"
    show_format_filters = True

    def get_queryset(self) -> BookQuerySet:
        books = super().get_queryset()
        books = books.filter(owned_by__username="sara") | books.filter(
            was_borrowed=True
        )
        return books


class UnreadIndexView(IndexView):
    filter_by = {"want_to_read": True}
    page_title = "To-Read Books"
    show_format_filters = True

    def get_queryset(self) -> BookQuerySet:
        books = (
            super()
            .get_queryset()
            .filter(Q(owned_by__isnull=False) | Q(edition_format=Book.Format["WEB"]))
            .exclude(tags__contains=["reference"])
        )
        return books


class SeriesIndexView(IndexView):
    sort_by = "series_order"

    def get_queryset(self) -> BookQuerySet:
        books = super().get_queryset()
        self.series = self.kwargs["series"].replace("%2f", "/")
        books = books.filter(series=self.series)
        return books

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context[
            "page_title"
        ] = f"{self.series} Series ({len(context['page_obj'])} books)"
        return context


class PublisherIndexView(IndexView):
    def get_queryset(self) -> BookQuerySet:
        books = super().get_queryset()
        self.publisher = self.kwargs["publisher"].replace("%2f", "/")
        books = books.filter(publisher=self.publisher)
        return books

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context[
            "page_title"
        ] = f"Books published by {self.publisher} ({self.get_queryset().count()} books)"
        return context


class TagIndexView(IndexView):
    def get_queryset(self) -> BookQuerySet:
        books = super().get_queryset()
        tags = [tag.strip() for tag in self.kwargs["tag_name"].split(",")]
        if tags == ["untagged"]:
            return books.filter(tags__len=0)
        elif len(tags) == 1 and tags[0].endswith("!"):
            tag = get_object_or_404(Tag, name=tags[0][0:-1])
            return tag.books_uniquely_tagged
        else:
            for tag in tags:
                books &= Tag.objects[tag].books_recursive
            return books

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["tags"] = [
            Tag.objects[tag]
            for tag in self.kwargs["tag_name"].split(",")
            if tag != "untagged"
        ]
        context[
            "page_title"
        ] = f"{self.get_queryset().count()} books tagged {oxford_comma(self.kwargs['tag_name'].split(','))}"
        return context


class ReviewedView(IndexView):
    page_title = "Reviewed Books"

    def get_queryset(self) -> BookQuerySet:
        return super().get_queryset().exclude(review="")


class UnreviewedView(IndexView):
    page_title = "Unreviewed Books"

    def get_queryset(self) -> BookQuerySet:
        return super().get_queryset().filter(review="").read()


class DetailView(LoginRequiredMixin, generic.DetailView):
    model = Book

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        context["page_title"] = book.display_title + " by " + str(book.first_author)
        return context


class GenericLogView(LoginRequiredMixin, generic.ListView):
    context_object_name = "entries"

    filter_by = {}
    page_title = ""

    def get_queryset(self) -> LogEntryQuerySet:
        entries = (
            LogEntry.objects.select_related("book", "book__first_author")
            .prefetch_related("book__additional_authors", "book__log_entries")
            .all()
            .order_by("end_date", "start_date")
        )

        if self.filter_by:
            entries = entries.filter(**self.filter_by)

        if year := self.kwargs.get("year"):
            if self.request.GET.get("infinite") == "true":
                self.page_title = None
            if year == "sometime" or str(year) == "1":
                ordering = [
                    Lower(F("book__first_author__surname")),
                    Lower(F("book__first_author__forenames")),
                    "book__series",
                    "book__series_order",
                    "book__title",
                ]
                entries = entries.filter(end_date__year=1).order_by(*ordering)
            else:
                entries = entries.filter(end_date__year=year)

        return entries.filter_by_request(self.request).distinct()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["year"] = self.kwargs.get("year")
        return context


class CurrentlyReadingView(GenericLogView):
    filter_by = {"end_date__isnull": True}
    page_title = "Currently Reading"

    def get_queryset(self) -> LogEntryQuerySet:
        return super().get_queryset().order_by("-progress_date", "start_date")


class ReadView(GenericLogView):
    filter_by = {"end_date__isnull": False}
    page_title = "Read Books"

    def get_queryset(self) -> LogEntryQuerySet:
        entries = super().get_queryset()
        if entries:
            year = entries.last().end_date.year
            return entries.filter(end_date__year=year)
        else:
            return LogEntry.objects.none()


class MarkdownReadView(GenericLogView):
    template_name = "logentry_list_markdown.md"
    content_type = "text/plain; charset=utf-8"
    filter_by = {"end_date__isnull": False}

    def get_queryset(self) -> LogEntryQuerySet:
        return (
            super()
            .get_queryset()
            .order_by(
                "-end_date__year",
                "end_date",
                "book__first_author__surname",
                "book__first_author__forenames",
                "book__series",
                "book__series_order",
                "book__title",
            )
        )


class XmlReadView(GenericLogView):
    template_name = "logentry_list_feed.xml"
    content_type = "application/xml; charset=utf-8"
    filter_by = {"end_date__isnull": False}

    def get_queryset(self) -> LogEntryQuerySet:
        return (
            super()
            .get_queryset()
            .order_by(
                "-end_date",
                "book__first_author__surname",
                "book__first_author__forenames",
                "book__series",
                "book__series_order",
                "book__title",
            )[0:20]
        )


@login_required
@require_POST
def start_reading(request: HttpRequest, slug: str) -> HttpResponse:
    book = get_object_or_404(Book, slug=slug)
    book.start_reading()
    return redirect("library:book_details", slug=slug)


@login_required
@require_POST
def finish_reading(request: HttpRequest, slug: str) -> HttpResponse:
    book = get_object_or_404(Book, slug=slug)
    book.finish_reading()
    return redirect("library:book_details", slug=slug)


@login_required
@require_POST
def update_progress(request: HttpRequest, slug: str) -> HttpResponse:
    book = get_object_or_404(Book, slug=slug)

    if request.POST["progress_type"] == "pages":
        page = int(request.POST["value"])
        percentage = None
    else:
        page = None
        percentage = float(request.POST["value"])

    percentage = book.update_progress(percentage=percentage, page=page)

    if page and book.page_count:
        progress_text = f"on page {page} of {book.page_count} ({percentage:.4g}% done)"
    else:
        progress_text = f"{percentage:.4g}% done"
    progress_text += f" on {timezone.now().strftime('%d %B, %Y')}"

    response = HttpResponse(
        json.dumps({"percentage": percentage, "progress_text": progress_text})
    )
    return response


@login_required
@require_POST
def add_tags(request: HttpRequest, slug: str) -> HttpResponse:
    book = get_object_or_404(Book, slug=slug)
    tags = request.POST.get("tags").split(",")

    if tags:
        start_tags = book.tags.copy()
        book.tags += tags
        book.save()
        tags = sorted(set(book.tags).difference(start_tags))

    return HttpResponse(json.dumps({"tags": tags}))


@login_required
@require_POST
def remove_tags(request: HttpRequest, slug: str) -> HttpResponse:
    book = get_object_or_404(Book, slug=slug)
    tags = request.POST.get("tags").split(",")
    for tag in tags:
        book.tags.remove(tag)
    book.save()

    if next := request.GET.get("next"):
        return redirect(next)
    else:
        return redirect("library:book_details", slug=slug)


@login_required
@require_POST
def mark_owned(request: HttpRequest, slug: str) -> HttpResponse:
    book = get_object_or_404(Book, slug=slug)
    book.mark_owned()
    return redirect("library:book_details", slug=slug)


@login_required
@require_POST
def mark_read_sometime(request: HttpRequest, slug: str) -> HttpResponse:
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


class CreateOrUpdateView(LoginRequiredMixin):
    form_class = BookForm
    model = Book

    def form_valid(self, form: BookForm) -> HttpResponse:
        context = self.get_context_data()
        self.object = form.save()

        if all([formset.is_valid() for formset in context["inline_formsets"]]):
            for formset in context["inline_formsets"]:
                formset.instance = self.object
                formset.save()

                for subform in formset:
                    if formset.data.get(subform.prefix + "-DELETE") == "on":
                        if subform.instance.id:
                            subform.instance.delete()

            return super(CreateOrUpdateView, self).form_valid(form)
        else:
            return super(CreateOrUpdateView, self).form_invalid(form)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super(CreateOrUpdateView, self).get_context_data(**kwargs)

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

        if self.object:
            context["page_title"] = f"Editing {self.object}"
        else:
            context["page_title"] = "New book"

        return context


class NewView(CreateOrUpdateView, generic.edit.CreateView):
    pass


class EditView(CreateOrUpdateView, generic.edit.UpdateView):
    pass


class DeleteView(LoginRequiredMixin, generic.edit.DeleteView):
    model = Book
    success_url = reverse_lazy("library:books_all")
    template_name = "confirm_delete.html"
