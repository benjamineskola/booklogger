from django.urls import include, path, re_path

from . import views

app_name = "library"
urlpatterns = [
    path("", views.book.CurrentlyReadingView.as_view(), name="index"),
    path("author/new/", views.author.NewView.as_view(), name="author_new"),
    path(
        "author/<slug:slug>/",
        include(
            [
                path("", views.author.DetailView.as_view(), name="author_details"),
                path("delete", views.author.DeleteView.as_view(), name="author_delete"),
                path("edit", views.author.EditView.as_view(), name="author_edit"),
            ]
        ),
    ),
    re_path(
        r"^authors(?:/(?P<page>d+))?/",
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
                path("add_tags/", views.book.add_tags, name="book_add_tags",),
                path("finish/", views.book.finish_reading, name="book_finish_reading",),
                path("start/", views.book.start_reading, name="book_start_reading",),
                path(
                    "update/", views.book.update_progress, name="book_update_progress",
                ),
                path("delete/", views.book.DeleteView.as_view(), name="book_delete"),
                path("edit/", views.book.EditView.as_view(), name="book_edit"),
                path("mark_owned/", views.book.mark_owned, name="book_mark_owned"),
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
                    r"^borrowed(?:/(?P<format>[a-z]+))?(?:/(?P<page>d+))?/",
                    views.book.BorrowedIndexView.as_view(),
                    name="books_borrowed",
                ),
                re_path(
                    r"^owned/bydate(?:/(?P<page>d+))?/",
                    views.book.OwnedIndexView.as_view(),
                    {"sort_by": "-acquired_date"},
                    name="books_owned_by_date",
                ),
                re_path(
                    r"^owned(?:/(?P<format>[a-z]+))?(?:/(?P<page>d+))?/",
                    views.book.OwnedIndexView.as_view(),
                    name="books_owned",
                ),
                re_path(
                    r"^read(?:/(?P<year>(\d+|sometime)))?/",
                    views.book.ReadView.as_view(),
                    name="books_read",
                ),
                re_path(
                    r"^reviewed(?:/(?P<page>d+))?/",
                    views.book.ReviewedView.as_view(),
                    name="books_reviewed",
                ),
                re_path(
                    r"^toread(?:/(?P<format>[a-z]+))?(?:/(?P<page>d+))?/",
                    views.book.UnreadIndexView.as_view(),
                    name="books_unread",
                ),
                re_path(
                    r"^unowned(?:/(?P<format>[a-z]+))?(?:/(?P<page>d+))?/",
                    views.book.IndexView.as_view(),
                    {
                        "filter_by": {"owned_by__isnull": True, "want_to_read": True},
                        "page_title": "Unowned Books",
                    },
                    name="books_unowned",
                ),
                re_path(
                    r"^unreviewed(?:/(?P<page>d+))?/",
                    views.book.UnreviewedView.as_view(),
                    name="books_unreviewed",
                ),
                re_path(
                    r"^(?:(?P<format>[a-z]+)/)?(?:(?P<page>d+)/)?",
                    views.book.IndexView.as_view(),
                    name="books_all",
                ),
            ]
        ),
    ),
    path("search/", views.basic_search, name="basic_search"),
    path("series/", views.series.list, name="series_index"),
    path(
        "series/<path:series>/",
        views.book.SeriesIndexView.as_view(),
        name="series_details",
    ),
    path("stats/", views.stats, name="stats"),
    path("tag/<str:tag_name>/", views.book.TagIndexView.as_view(), name="tag_details"),
    path("tags/", views.tag_cloud, name="tag_cloud"),
    re_path(r"^report(?:/(?P<page>d+))?/", views.report.report, name="report"),
    path("bulkimport/", views.importer.bulk_import, name="bulk_import"),
]
