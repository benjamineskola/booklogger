from django.urls import include, path, re_path

from . import views

app_name = "library"
urlpatterns = [
    path("", views.book.CurrentlyReadingView.as_view(), name="index"),
    path("robots.txt", views.robots_txt),
    re_path(r".*/[^./]+[^/]$", views.add_slash),
    path("author/new/", views.author.NewView.as_view(), name="author_new"),
    path(
        "author/<slug:slug>/",
        include(
            [
                path("", views.author.DetailView.as_view(), name="author_details"),
                path(
                    "delete/", views.author.DeleteView.as_view(), name="author_delete"
                ),
                path("edit/", views.author.EditView.as_view(), name="author_edit"),
            ]
        ),
    ),
    re_path(
        r"^authors(?:/(?P<page>\d+))?/",
        views.author.IndexView.as_view(),
        name="author_list",
    ),
    re_path(
        r"^book/import/(?:(?P<query>\w+)/)?",
        views.importer.import_book,
        name="book_import",
    ),
    path("book/new/", views.book.NewView.as_view(), name="book_new"),
    path(
        "book/<slug:slug>/",
        include(
            [
                path("", views.book.DetailView.as_view(), name="book_details"),
                path(
                    "add_tags/",
                    views.book.add_tags,
                    name="book_add_tags",
                ),
                path(
                    "remove_tags/",
                    views.book.remove_tags,
                    name="book_remove_tags",
                ),
                path(
                    "finish/",
                    views.book.finish_reading,
                    name="book_finish_reading",
                ),
                path(
                    "start/",
                    views.book.start_reading,
                    name="book_start_reading",
                ),
                path(
                    "update/",
                    views.book.update_progress,
                    name="book_update_progress",
                ),
                path("delete/", views.book.DeleteView.as_view(), name="book_delete"),
                path("edit/", views.book.EditView.as_view(), name="book_edit"),
                path("mark_owned/", views.book.mark_owned, name="book_mark_owned"),
                path(
                    "mark_read_sometime/",
                    views.book.mark_read_sometime,
                    name="book_mark_read_sometime",
                ),
                path("rate/", views.book.rate, name="book_rate"),
            ]
        ),
    ),
    path(
        "books/",
        include(
            [
                path(
                    "reading/",
                    views.book.CurrentlyReadingView.as_view(),
                    name="books_currently_reading",
                ),
                re_path(
                    r"^borrowed(?:/(?P<format>[a-z]+))?(?:/(?P<page>\d+))?/",
                    views.book.BorrowedIndexView.as_view(),
                    name="books_borrowed",
                ),
                re_path(
                    r"^owned/bydate(?:/(?P<page>\d+))?/",
                    views.book.OwnedIndexView.as_view(),
                    {"sort_by": "acquired_date", "show_format_filters": False},
                    name="books_owned_by_date",
                ),
                re_path(
                    r"^owned(?:/(?P<format>[a-z]+))?(?:/(?P<page>\d+))?/",
                    views.book.OwnedIndexView.as_view(),
                    name="books_owned",
                ),
                re_path(
                    r"^read(?:/(?P<year>(\d+|sometime)))?\.md",
                    views.book.MarkdownReadView.as_view(),
                    name="books_read_markdown",
                ),
                re_path(
                    r"^read\.xml",
                    views.book.XmlReadView.as_view(),
                    name="books_read_xml",
                ),
                re_path(
                    r"^read(?:/(?P<year>(\d+|sometime)))?/",
                    views.book.ReadView.as_view(),
                    name="books_read",
                ),
                re_path(
                    r"^reviewed(?:/(?P<page>\d+))?/",
                    views.book.ReviewedView.as_view(),
                    name="books_reviewed",
                ),
                re_path(
                    r"^toread(?:/(?P<format>[a-z]+))?(?:/(?P<page>\d+))?/",
                    views.book.UnreadIndexView.as_view(),
                    name="books_to_read",
                ),
                re_path(
                    r"^unowned(?:/(?P<format>[a-z]+))?(?:/(?P<page>\d+))?/",
                    views.book.IndexView.as_view(),
                    {
                        "filter_by": {"owned_by__isnull": True, "want_to_read": True},
                        "page_title": "Unowned Books",
                    },
                    name="books_unowned",
                ),
                re_path(
                    r"^unreviewed(?:/(?P<page>\d+))?/",
                    views.book.UnreviewedView.as_view(),
                    name="books_unreviewed",
                ),
                re_path(
                    r"^(?:(?P<format>[a-z]+)/)?(?:(?P<page>\d+)/)?",
                    views.book.IndexView.as_view(),
                    name="books_all",
                ),
            ]
        ),
    ),
    path("lists/", views.reading_list.IndexView.as_view(), name="list_index"),
    path(
        "list/<str:pk>/", views.reading_list.DetailView.as_view(), name="list_details"
    ),
    path("search/", views.search.basic_search, name="basic_search"),
    path("series/", views.series.list, name="series_index"),
    path(
        "series/<path:series>/",
        views.book.SeriesIndexView.as_view(),
        name="series_details",
    ),
    path("publishers/", views.publisher.list, name="publisher_index"),
    re_path(
        r"^publisher(?:/(?P<publisher>[^/]+))?(?:/(?P<page>\d+))?/",
        views.book.PublisherIndexView.as_view(),
        name="publisher_details",
    ),
    path("stats/", views.stats_index, name="stats"),
    path("stats/<str:year>/", views.stats_for_year, name="stats_for_year"),
    re_path(
        r"^tag(?:/(?P<tag_name>[^/]+))?(?:/(?P<page>\d+))?/",
        views.book.TagIndexView.as_view(),
        name="tag_details",
    ),
    path("tags/", views.tag_cloud, name="tag_cloud"),
    re_path(
        r"^report/tags/related(?:/(?P<base_tag>[^/]+))?/",
        views.report.related_tags,
        name="report_related_tags",
    ),
    re_path(
        r"^report/tags(?:/(?P<base_tag>[^/]+))?/", views.report.tags, name="report_tags"
    ),
    re_path(r"^report(?:/(?P<page>\d+))?/", views.report.report, name="report"),
    path("bulkimport/", views.importer.bulk_import, name="bulk_import"),
]
