from django.views import generic

from library.models import Author


class DetailView(generic.DetailView):
    model = Author
    template_name = "authors/details.html"


class IndexView(generic.ListView):
    template_name = "authors/list.html"
    context_object_name = "authors"
    paginate_by = 100
    queryset = Author.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_authors"] = self.queryset.count()
        return context
