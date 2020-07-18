from itertools import groupby

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.views.decorators.http import require_POST

from library.forms import BookAuthorFormSet, BookForm
from library.models import Book, LogEntry
from library.utils import oxford_comma


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
            books = books.filter_by_format(edition_format)

        if sort_by := self.request.GET.get("sort_by"):
            field_names = [f.name for f in Book._meta.get_fields()]
            if sort_by.startswith("-") and sort_by[1:] in field_names:
                books = books.order_by(F(sort_by[1:]).desc(nulls_last=True))
            elif sort_by in field_names:
                books = books.order_by(sort_by)

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
        context["page_title"] = self.page_title + f" ({context['stats']['total']})"
        return context


class IndexView(GenericIndexView):
    page_title = "All Books"


class OwnedIndexView(GenericIndexView):
    filter_by = {"owned_by__username": "ben"}
    page_title = "Owned Books"

    def get_queryset(self):
        return super().get_queryset()


class OwnedByDateView(GenericIndexView):
    template_name = "books/list_by_date.html"
    filter_by = {"owned_by__username": "ben"}
    page_title = "Owned Books by Date"

    def get_queryset(self):
        books = (
            super()
            .get_queryset()
            .order_by(F("acquired_date").desc(nulls_last=True), *Book._meta.ordering)
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
    filter_by = {"owned_by__isnull": True, "want_to_read": True}
    page_title = "Unowned Books"


class BorrowedIndexView(GenericIndexView):
    page_title = "Borrowed Books"

    def get_queryset(self):
        books = super().get_queryset()
        books = books.filter(owned_by__username="sara") | books.filter(
            was_borrowed=True
        )
        return books


class UnreadIndexView(GenericIndexView):
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


class SeriesIndexView(GenericIndexView):
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


class TagIndexView(GenericIndexView):
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

        if year := self.kwargs.get("year"):
            entries = entries.filter(end_date__year=year)
            if year == 1:
                self.page_title = "Read sometime"
            else:
                self.page_title = f"Read in {year}"

        if self.filter_by:
            entries = entries.filter(**self.filter_by)
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
    progress = 0
    if request.POST["pages"] and book.page_count:
        progress = int(int(request.POST["pages"]) / book.page_count * 100)
    elif request.POST["percentage"]:
        progress = int(request.POST["percentage"])
    if progress:
        book.update_progress(progress)
    return redirect("library:book_details", slug=slug)


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


class CreateOrUpdateView(LoginRequiredMixin):
    template_name = "books/edit_form.html"
    form_class = BookForm
    model = Book

    def form_valid(self, form):
        context = self.get_context_data()
        inline_formset = context["inline_formset"]
        self.object = form.save()

        if inline_formset.is_valid():
            inline_formset.instance = self.object
            inline_formset.save()
            for subform in inline_formset:
                if inline_formset.data.get(subform.prefix + "-DELETE") == "on":
                    subform.instance.delete()

            return super(CreateOrUpdateView, self).form_valid(form)
        else:
            for subform in inline_formset:
                subform.set_delete_classes()
            return super(CreateOrUpdateView, self).form_invalid(form)

    def get_context_data(self, *args, **kwargs):
        context = super(CreateOrUpdateView, self).get_context_data(**kwargs)

        if self.request.POST:
            context["inline_formset"] = BookAuthorFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context["inline_formset"] = BookAuthorFormSet(instance=self.object)

        for subform in context["inline_formset"]:
            subform.fields["DELETE"].widget.attrs["class"] = "form-control"

        return context


class NewView(CreateOrUpdateView, generic.edit.CreateView):
    pass


class EditView(CreateOrUpdateView, generic.edit.UpdateView):
    pass


class DeleteView(LoginRequiredMixin, generic.edit.DeleteView):
    model = Book
    success_url = reverse_lazy("library:books_all")
    template_name = "confirm_delete.html"
