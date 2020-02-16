from itertools import groupby

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.views.decorators.http import require_POST

from library.models import Author, Book, BookAuthor, LogEntry


class GenericIndexView(generic.ListView):
    template_name = "books/list.html"
    paginate_by = 100

    filter_by = {}
    page_title = ""

    def get_queryset(self):
        books = (
            Book.objects.select_related("first_author")
            .prefetch_related("additional_authors", "log_entries")
            .all()
        )
        if self.filter_by:
            books = books.filter(**self.filter_by)

        if edition_format := self.kwargs.get("format"):
            edition_format = edition_format.strip("s").upper()
            books = books.filter(edition_format=Book.Format[edition_format])

        return books.filter_by_request(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["formats"] = Book.Format.choices
        context["format"] = self.kwargs.get("format")
        context["total"] = self.get_queryset().count()
        context["counts"] = {
            x: len(list(y))
            for x, y in groupby(
                self.get_queryset().order_by("edition_format"),
                lambda b: b.edition_format,
            )
        }
        context["page_title"] = self.page_title + f" ({context['total']})"
        return context


class IndexView(GenericIndexView):
    page_title = "All Books"


class OwnedIndexView(GenericIndexView):
    filter_by = {"owned": True}
    page_title = "Owned Books"
    template_name = "books/list_by_format.html"

    def get_queryset(self):
        return super().get_queryset().order_by("edition_format")


class OwnedByDateView(GenericIndexView):
    template_name = "books/list_by_date.html"
    filter_by = {"owned": True}

    def get_queryset(self):
        books = (
            super().get_queryset().order_by(F("acquired_date").desc(nulls_last=True))
        )
        return books

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["page_groups"] = [
            (d, list(l))
            for d, l in groupby(
                context["page_obj"].object_list, lambda b: b.acquired_date or "Undated"
            )
        ]

        return context


class UnownedIndexView(GenericIndexView):
    filter_by = {"owned": False, "want_to_read": True}
    page_title = "Unowned Books"


class BorrowedIndexView(GenericIndexView):
    filter_by = {"was_borrowed": True}
    page_title = "Borrowed Books"


class UnreadIndexView(GenericIndexView):
    filter_by = {"want_to_read": True}
    page_title = "Unread Books"
    template_name = "books/list_by_format.html"

    def get_queryset(self):
        books = super().get_queryset()
        books = (
            books.filter(owned=True)
            | books.filter(was_borrowed=True, borrowed_from="Sara")
            | books.filter(was_borrowed=True, borrowed_from="public domain")
            | books.filter(edition_format=Book.Format["WEB"])
        )
        return books.order_by(
            "edition_format",
            "first_author__single_name",
            "first_author__surname",
            "first_author__forenames",
            "title",
        )


class DetailView(generic.DetailView):
    model = Book
    template_name = "books/details.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        context["page_title"] = book.display_title + " by " + str(book.first_author)
        return context


class GenericLogView(generic.ListView):
    template_name = "logentries/list.html"
    context_object_name = "entries"

    filter_by = {}
    page_title = ""

    def get_queryset(self, *args, **kwargs):
        entries = (
            LogEntry.objects.select_related("book", "book__first_author")
            .prefetch_related("book__additional_authors", "book__log_entries")
            .all()
            .order_by("end_date", "start_date")
        )

        if "year" in self.kwargs:
            entries = entries.filter(end_date__year=self.kwargs["year"])
            self.page_title = f"Read in {self.kwargs['year']}"

        if self.filter_by:
            entries = entries.filter(**self.filter_by)
        return entries.filter_by_request(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        return context


class CurrentlyReadingView(GenericLogView):
    filter_by = {"end_date__isnull": True}
    page_title = "Currently Reading"

    def get_queryset(self, *args, **kwargs):
        return (
            super()
            .get_queryset(*args, **kwargs)
            .order_by("-progress_date", "start_date")
        )


class ReadView(GenericLogView):
    filter_by = {"end_date__isnull": False}
    page_title = "Read Books"


@login_required
@require_POST
def start_reading(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.start_reading()
    return redirect("library:book_details", pk=pk)


@login_required
@require_POST
def finish_reading(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.finish_reading()
    return redirect("library:book_details", pk=pk)


@login_required
@require_POST
def update_progress(request, pk):
    book = get_object_or_404(Book, pk=pk)
    progress = 0
    if request.POST["pages"] and book.page_count:
        progress = int(int(request.POST["pages"]) / book.page_count * 100)
    elif request.POST["percentage"]:
        progress = int(request.POST["percentage"])
    if progress:
        book.update_progress(progress)
    return redirect("library:book_details", pk=pk)


@login_required
@require_POST
def add_tags(request, pk):
    book = get_object_or_404(Book, pk=pk)
    for tag in request.POST.get("tags").split(","):
        clean_tag = tag.strip()
        if not clean_tag in book.tags:
            book.tags.append(clean_tag)
    book.save()

    if next := request.GET.get("next"):
        return redirect(next)
    else:
        return redirect("library:book_details", pk=pk)
