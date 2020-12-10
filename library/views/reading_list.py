from django.views import generic

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
