from django.views import generic

from library.models import Author


class DetailView(generic.DetailView):
    model = Author
    template_name = "authors/details.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = str(self.get_object())
        return context


class IndexView(generic.ListView):
    template_name = "authors/list.html"
    model = Author
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_authors"] = self.get_queryset().count()
        context["page_title"] = "Authors"
        return context
