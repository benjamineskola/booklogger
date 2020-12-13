from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views import generic

from library.forms import ReadingListForm
from library.models import ReadingList


class IndexView(generic.ListView):
    model = ReadingList

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({"page_title": "Reading Lists"})

        return context


class DetailView(generic.DetailView):
    model = ReadingList

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({"page_title": self.object.title})

        return context


class CreateOrUpdateView(LoginRequiredMixin):
    form_class = ReadingListForm
    model = ReadingList


class NewView(CreateOrUpdateView, generic.edit.CreateView):
    pass


class EditView(CreateOrUpdateView, generic.edit.UpdateView):
    pass


class DeleteView(LoginRequiredMixin, generic.edit.DeleteView):
    model = ReadingList
    success_url = reverse_lazy("library:list_index")
    template_name = "confirm_delete.html"
