import re
import json
from itertools import groupby

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic
from django.views.decorators.http import require_POST
from library.forms import BookAuthorFormSet, BookForm, LogEntryFormSet
from library.models import Book, LogEntry
from library.utils import oxford_comma


class IndexView(generic.ListView):
    paginate_by = 100

    filter_by = {}
    sort_by = None
    page_title = "All Books"

    def get_queryset(self):
        books = (
            Book.objects.select_related("first_author")
            .prefetch_related("additional_authors", "log_entries")
            .all()
        )

        if "filter_by" in self.kwargs:
            self.filter_by = self.kwargs["filter_by"]

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
                reverse_sort = True
            else:
                reverse_sort = False

            if self.sort_by in field_names:
                if self.sort_by == "read_date":
                    self.sort_by = "log_entries__end_date"

                if reverse_sort:
                    books = books.order_by(
                        F(self.sort_by).desc(nulls_last=True), *Book._meta.ordering
                    )
                else:
                    books = books.order_by(self.sort_by, *Book._meta.ordering)

        return books.filter_by_request(self.request).distinct()

    def get_context_data(self, **kwargs):
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

        if "page_title" in self.kwargs:
            self.page_title = self.kwargs["page_title"]
        context["page_title"] = self.page_title + f" ({context['stats']['total']})"
        if self.sort_by:
            context["page_title"] += f" by {re.sub(r'_', ' ', self.sort_by.title())}"

            if self.sort_by in ["edition_format", "rating"] or "date" in self.sort_by:
                self.template_name = "book_list_grouped.html"
                context["group_by"] = self.sort_by
                context["page_groups"] = [
                    (d, list(l))
                    for d, l in groupby(
                        context["page_obj"].object_list,
                        lambda b: getattr(b, self.sort_by) or None,
                    )
                ]

        return context


class OwnedIndexView(IndexView):
    filter_by = {"owned_by__username": "ben"}
    page_title = "Owned Books"


class BorrowedIndexView(IndexView):
    page_title = "Borrowed Books"

    def get_queryset(self):
        books = super().get_queryset()
        books = books.filter(owned_by__username="sara") | books.filter(
            was_borrowed=True
        )
        return books


class UnreadIndexView(IndexView):
    filter_by = {"want_to_read": True}
    page_title = "Unread Books"

    def get_queryset(self):
        books = (
            super()
            .get_queryset()
            .filter(Q(owned_by__isnull=False) | Q(edition_format=Book.Format["WEB"]))
            .exclude(tags__contains=["reference"])
        )
        return books


class SeriesIndexView(IndexView):
    sort_by = "series_order"

    def get_queryset(self):
        books = super().get_queryset()
        books = books.filter(series=self.kwargs["series"])
        return books

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[
            "page_title"
        ] = f"{self.kwargs['series']} Series ({len(context['page_obj'])} books)"
        return context


class TagIndexView(IndexView):
    def get_queryset(self):
        books = super().get_queryset()
        tags = [tag.strip() for tag in self.kwargs["tag_name"].split(",")]
        if tags == ["untagged"]:
            condition = {"tags__len": 0}
        elif len(tags) == 1 and tags[0].endswith("!"):
            condition = {"tags": [tags[0][0:-1]]}
        else:
            condition = {"tags__contains": tags}
        books = books.filter(**condition)
        return books

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[
            "page_title"
        ] = f"{self.get_queryset().count()} books tagged {oxford_comma(self.kwargs['tag_name'].split(','))}"
        return context


class ReviewedView(IndexView):
    page_title = "Reviewed Books"

    def get_queryset(self):
        return super().get_queryset().exclude(review="")


class UnreviewedView(IndexView):
    page_title = "Unreviewed Books"

    def get_queryset(self):
        return super().get_queryset().filter(review="").read()


class DetailView(generic.DetailView):
    model = Book

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        context["page_title"] = book.display_title + " by " + str(book.first_author)
        return context


class GenericLogView(generic.ListView):
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

        if self.filter_by:
            entries = entries.filter(**self.filter_by)

        if year := self.kwargs.get("year"):
            if year == "sometime" or str(year) == "1":
                ordering = [
                    Lower(F("book__first_author__surname")),
                    Lower(F("book__first_author__forenames")),
                    "book__series",
                    "book__series_order",
                    "book__title",
                ]
                self.page_title = "Read sometime"
                entries = entries.filter(end_date__year=1).order_by(*ordering)
            else:
                self.page_title = f"Read in {year}"
                entries = entries.filter(end_date__year=year)

        return entries.filter_by_request(self.request).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["year"] = self.kwargs.get("year")
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

    def get_queryset(self, *args, **kwargs):
        entries = super().get_queryset(*args, **kwargs)
        year = entries.last().end_date.year
        return entries.filter(end_date__year=year)


@login_required
@require_POST
def start_reading(request, slug):
    book = get_object_or_404(Book, slug=slug)
    book.start_reading()
    return redirect("library:book_details", slug=slug)


@login_required
@require_POST
def finish_reading(request, slug):
    book = get_object_or_404(Book, slug=slug)
    book.finish_reading()
    return redirect("library:book_details", slug=slug)


@login_required
@require_POST
def update_progress(request, slug):
    book = get_object_or_404(Book, slug=slug)

    if request.POST["progress_type"] == "pages":
        page = int(request.POST["value"])
        percentage = None
    else:
        page = None
        percentage = int(request.POST["value"])

    percentage = book.update_progress(percentage=percentage, page=page)

    if page and book.page_count:
        progress_text = f"on page {page} of {book.page_count} ({percentage}% done)"
    else:
        progress_text = f"{percentage}% done"
    progress_text += f" on {timezone.now().strftime('%d %B, %Y')}"

    response = HttpResponse(
        json.dumps({"percentage": percentage, "progress_text": progress_text})
    )
    return response


@login_required
@require_POST
def add_tags(request, slug):
    book = get_object_or_404(Book, slug=slug)
    tags = request.POST.get("tags").split(",")
    if tags:
        book.add_tags(tags)

    if next := request.GET.get("next"):
        return redirect(next)
    else:
        return redirect("library:book_details", slug=slug)


@login_required
@require_POST
def mark_owned(request, slug):
    book = get_object_or_404(Book, slug=slug)
    book.mark_owned()
    return redirect("library:book_details", slug=slug)


@login_required
@require_POST
def rate(request, slug):
    book = get_object_or_404(Book, slug=slug)
    if rating := request.POST["rating"]:
        book.rating = rating
        book.save()

    return redirect("library:book_details", slug=slug)


class CreateOrUpdateView(LoginRequiredMixin):
    form_class = BookForm
    model = Book

    def form_valid(self, form):
        context = self.get_context_data()
        bookauthor_formset = context["bookauthor_formset"]
        logentry_formset = context["logentry_formset"]
        self.object = form.save()

        if bookauthor_formset.is_valid() and logentry_formset.is_valid():
            bookauthor_formset.instance = self.object
            bookauthor_formset.save()
            logentry_formset.instance = self.object
            logentry_formset.save()

            for subform in bookauthor_formset:
                if bookauthor_formset.data.get(subform.prefix + "-DELETE") == "on":
                    if subform.instance.id:
                        subform.instance.delete()
            for subform in logentry_formset:
                if logentry_formset.data.get(subform.prefix + "-DELETE") == "on":
                    if subform.instance.id:
                        subform.instance.delete()

            return super(CreateOrUpdateView, self).form_valid(form)
        else:
            return super(CreateOrUpdateView, self).form_invalid(form)

    def get_context_data(self, *args, **kwargs):
        context = super(CreateOrUpdateView, self).get_context_data(**kwargs)

        if self.request.POST:
            context["bookauthor_formset"] = BookAuthorFormSet(
                self.request.POST, instance=self.object
            )
            context["logentry_formset"] = LogEntryFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context["bookauthor_formset"] = BookAuthorFormSet(instance=self.object)
            context["logentry_formset"] = LogEntryFormSet(instance=self.object)

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
