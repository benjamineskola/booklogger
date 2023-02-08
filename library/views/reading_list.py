from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views import generic

from library.forms import ReadingListForm
from library.models import ReadingList


class IndexView(generic.ListView[ReadingList]):
    model = ReadingList

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "Reading lists"})

        return context


class DetailView(generic.DetailView[ReadingList]):
    model = ReadingList

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({"page_title": self.object.title})

        return context


class NewView(
    LoginRequiredMixin, generic.edit.CreateView[ReadingList, ReadingListForm]
):
    form_class = ReadingListForm
    model = ReadingList


class EditView(
    LoginRequiredMixin, generic.edit.UpdateView[ReadingList, ReadingListForm]
):
    form_class = ReadingListForm
    model = ReadingList


class DeleteView(
    LoginRequiredMixin, generic.edit.DeleteView[ReadingList, ReadingListForm]
):
    model = ReadingList
    object: ReadingList  # noqa: A003
    success_url = reverse_lazy("library:list_index")
    template_name = "confirm_delete.html"
