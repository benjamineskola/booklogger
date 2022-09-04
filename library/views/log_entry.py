from datetime import datetime
from typing import Any

from django.contrib.syndication.views import Feed
from django.db.models import F
from django.db.models.functions import Lower
from django.http import HttpRequest
from django.utils.feedgenerator import Atom1Feed
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
        elif self.single_year and (last := entries.last()) and last.end_date:
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


class XmlReadView(Feed[Any, Any]):
    feed_type = Atom1Feed
    title = "Ben's Read Books"
    link = "/books/read/"
    description_template = "logentry_item.xml"

    def get_object(self, request: HttpRequest) -> LogEntryQuerySet:  # type: ignore [override]
        return (
            LogEntry.objects.select_related("book", "book__first_author")
            .prefetch_related("book__additional_authors", "book__log_entries")
            .filter(
                book__private__in=(
                    [True, False] if is_authenticated(request) else [False]
                )
            )
            .filter(end_date__isnull=False, abandoned=False)
            .order_by(
                "-end_date",
                Lower(F("book__first_author__surname")),
                Lower(F("book__first_author__forenames")),
                "book__series",
                "book__series_order",
                "book__title",
            )
        )

    def items(self, obj: LogEntryQuerySet) -> LogEntryQuerySet:
        return obj[0:50]

    def item_link(self, item: LogEntry) -> str:
        return item.book.get_absolute_url()

    def item_guid(self, item: LogEntry) -> str:
        if not item.end_date:
            return "???"

        return f"tag:booklogger.eskola.uk,2020-11-27:{ item.end_date.strftime('%Y-%m-%d') }/{ item.book.slug }"

    def item_pubdate(self, item: LogEntry) -> datetime | None:
        if item.end_date:
            return item.end_date

        return None

    def item_updateddate(self, item: LogEntry) -> datetime | None:
        return self.item_pubdate(item)

    def item_title(self, item: LogEntry) -> str:
        return f"Finished reading { item.book.display_title }"

    def item_enclosure_url(self, item: LogEntry) -> str:
        return item.book.image_url

    item_enclosure_mime_type = "image/jpeg"

    def item_categories(self, item: LogEntry) -> list[str]:
        return [str(tag) for tag in item.book.tags.all()]
