from typing import Any, Dict, Type

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views import generic

from library.forms import ReadingListForm
from library.models import ReadingList


class IndexView(generic.ListView[ReadingList]):
    model = ReadingList

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "Reading Lists"})

        return context


class DetailView(generic.DetailView[ReadingList]):
    model = ReadingList

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({"page_title": self.object.title})  # type: ignore [attr-defined]

        return context


class CreateOrUpdateView(LoginRequiredMixin):
    form_class: Type[ReadingListForm]
    model: Type[ReadingList]


class NewView(
    CreateOrUpdateView, generic.edit.CreateView[ReadingList, ReadingListForm]
):
    form_class: Type[ReadingListForm]
    model: Type[ReadingList]


class EditView(
    CreateOrUpdateView, generic.edit.UpdateView[ReadingList, ReadingListForm]
):
    form_class: Type[ReadingListForm]
    model: Type[ReadingList]


class DeleteView(LoginRequiredMixin, generic.edit.DeleteView):
    model = ReadingList
    success_url = reverse_lazy("library:list_index")
    template_name = "confirm_delete.html"
