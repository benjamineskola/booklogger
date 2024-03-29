import math
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpRequest, JsonResponse
from django.urls import reverse_lazy
from django.views import generic

from library.forms import AuthorForm
from library.models import Author


class DetailView(generic.DetailView[Author]):
    model = Author

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = str(self.get_object())
        context["books"] = self.get_object().books.filter(
            private__in=(
                [True, False] if self.request.user.is_authenticated else [False]
            )
        )
        context["books"] = context["books"].filter_by_request(self.request)

        if edition_format := self.request.GET.get("format"):
            context["books"] = context["books"].filter_by_format(edition_format)

        return context


class IndexView(generic.ListView[Author]):
    model = Author
    paginate_by = 100

    def get_queryset(self) -> QuerySet[Author]:
        qs: QuerySet[Author] = super().get_queryset()  # type: ignore[assignment]
        if gender := self.request.GET.get("gender"):
            if not gender.isnumeric():
                gender = str(Author.Gender[gender.upper()])
            qs = qs.filter(gender=gender)
        if poc := self.request.GET.get("poc"):
            if poc.lower() in ["1", "true"]:
                qs = qs.filter(poc=True)
            elif poc.lower() in ["0", "false"]:
                qs = qs.filter(poc=False)

        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["total_authors"] = self.get_queryset().count()
        context["page_title"] = "Authors"
        if gender := self.request.GET.get("gender"):
            if gender.isnumeric():
                gender = Author.Gender.choices[int(gender)][1].lower()
            context["gender"] = gender
        if poc := self.request.GET.get("poc"):
            if poc.lower() in ["1", "true"]:
                context["poc"] = "poc"
            elif poc.lower() in ["0", "false"]:
                context["poc"] = "white"

        return context


class EditView(LoginRequiredMixin, generic.edit.UpdateView[Author, AuthorForm]):
    form_class = AuthorForm
    model = Author

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Editing {self.object}"
        return context


class NewView(LoginRequiredMixin, generic.edit.CreateView[Author, AuthorForm]):
    form_class = AuthorForm
    model = Author

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New author"
        return context


class DeleteView(LoginRequiredMixin, generic.edit.DeleteView[Author, AuthorForm]):
    model = Author
    object: Author  # noqa: A003
    success_url = reverse_lazy("library:author_list")
    template_name = "confirm_delete.html"


def export_authors(request: HttpRequest) -> JsonResponse:
    page = int(request.GET.get("page", 1))
    count = 100
    start = (page - 1) * 100
    authors = Author.objects.all()[start : start + count]
    result = {
        "page": page,
        "per_page": count,
        "total": Author.objects.count(),
        "total_pages": math.ceil(Author.objects.count() / count),
        "this_page": authors.count(),
        "authors": [author.to_json() for author in authors if author.books.count()],
    }

    return JsonResponse(result)
