from typing import Any

from django.db.models import F
from django.db.models.functions import Lower
from django.views import generic

from library.models import LogEntry, LogEntryQuerySet
from library.utils import is_authenticated


class GenericLogView(generic.ListView[LogEntry]):
    context_object_name = "entries"

    filter_by: dict[str, Any] = {}
    page_title = ""
    reverse_sort = False
    single_year = False

    def get_queryset(self) -> LogEntryQuerySet:
        entries = (
            LogEntry.objects.select_related("book", "book__first_author")
            .prefetch_related("book__additional_authors", "book__log_entries")
            .filter(
                book__private__in=(
                    [True, False] if is_authenticated(self.request) else [False]
                )
            )
            .order_by(
                "-end_date" if self.reverse_sort else "end_date",
                Lower(F("book__first_author__surname")),
                Lower(F("book__first_author__forenames")),
                "book__series",
                "book__series_order",
                "book__title",
            )
        )

        if self.filter_by:
            entries = entries.filter(**self.filter_by)

        if year := self.kwargs.get("year"):
            if self.request.GET.get("infinite") == "true":
                self.page_title = ""
            if year == "sometime" or str(year) == "1":
                entries = entries.filter(end_date__year=1)
            else:
                entries = entries.filter(end_date__year=year)
        elif self.single_year:
            if (last := entries.last()) and last.end_date:
                entries = entries.filter(end_date__year=last.end_date.year)

        return entries.filter_by_request(self.request).distinct()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["year"] = self.kwargs.get("year")
        context["verbose"] = "verbose" in self.request.GET
        return context


class CurrentlyReadingView(GenericLogView):
    filter_by = {"end_date__isnull": True}
    page_title = "Currently Reading"

    def get_queryset(self) -> LogEntryQuerySet:
        return super().get_queryset().order_by("-progress_date", "start_date")


class ReadView(GenericLogView):
    filter_by = {"end_date__isnull": False, "abandoned": False}
    page_title = "Read Books"
    single_year = True


class MarkdownReadView(ReadView):
    template_name = "logentry_list_markdown.md"
    content_type = "text/plain; charset=utf-8"
    single_year = False


class XmlReadView(ReadView):
    template_name = "logentry_list_feed.xml"
    content_type = "application/xml; charset=utf-8"
    reverse_sort = True
    single_year = False

    def get_queryset(self) -> LogEntryQuerySet:
        return super().get_queryset()[0:20]
