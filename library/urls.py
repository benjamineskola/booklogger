from django.urls import include, path

from . import views

app_name = "library"
urlpatterns = [
    path("", views.book.CurrentlyReadingView.as_view(), name="index"),
    path("author/new/", views.author.new, name="author_new"),
    path(
        "author/<slug:slug>/",
        include(
            [
                path("", views.author.DetailView.as_view(), name="author_details"),
                path("edit", views.author.edit, name="author_edit"),
            ]
        ),
    ),
    path("authors/", views.author.IndexView.as_view(), name="author_list"),
    path("authors/<int:page>/", views.author.IndexView.as_view(), name="author_list"),
    path("book/import/", views.import_book, name="book_import"),
    path("book/import/<str:query>/", views.import_book, name="book_import"),
    path("book/new/", views.book.new, name="book_new"),
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
                path("edit/", views.book.edit, name="book_edit"),
                path("mark_owned/", views.book.mark_owned, name="book_mark_owned"),
            ]
        ),
    ),
    path(
        "books/",
        include(
            [
                path("", views.book.IndexView.as_view(), name="books_all"),
                path("<int:page>/", views.book.IndexView.as_view(), name="books_all"),
                path(
                    "borrowed/",
                    views.book.BorrowedIndexView.as_view(),
                    name="books_borrowed",
                ),
                path(
                    "borrowed/<int:page>",
                    views.book.BorrowedIndexView.as_view(),
                    name="books_borrowed",
                ),
                path(
                    "borrowed/<str:format>/",
                    views.book.BorrowedIndexView.as_view(),
                    name="books_borrowed",
                ),
                path(
                    "borrowed/<str:format>/<int:page>/",
                    views.book.BorrowedIndexView.as_view(),
                    name="books_borrowed",
                ),
                path("owned/", views.book.OwnedIndexView.as_view(), name="books_owned"),
                path(
                    "owned/<int:page>/",
                    views.book.OwnedIndexView.as_view(),
                    name="books_owned",
                ),
                path(
                    "owned/bydate/",
                    views.book.OwnedByDateView.as_view(),
                    name="books_owned_by_date",
                ),
                path(
                    "owned/bydate/<int:page>/",
                    views.book.OwnedByDateView.as_view(),
                    name="books_owned_by_date",
                ),
                path(
                    "owned/<str:format>/",
                    views.book.OwnedIndexView.as_view(),
                    name="books_owned",
                ),
                path(
                    "owned/<str:format>/<int:page>/",
                    views.book.OwnedIndexView.as_view(),
                    name="books_owned",
                ),
                path("read/", views.book.ReadView.as_view(), name="books_read"),
                path(
                    "read/<int:year>/", views.book.ReadView.as_view(), name="books_read"
                ),
                path(
                    "reading/",
                    views.book.CurrentlyReadingView.as_view(),
                    name="books_currently_reading",
                ),
                path(
                    "toread/", views.book.UnreadIndexView.as_view(), name="books_unread"
                ),
                path(
                    "toread/<int:page>/",
                    views.book.UnreadIndexView.as_view(),
                    name="books_unread",
                ),
                path(
                    "toread/<str:format>/",
                    views.book.UnreadIndexView.as_view(),
                    name="books_unread",
                ),
                path(
                    "toread/<str:format>/<int:page>/",
                    views.book.UnreadIndexView.as_view(),
                    name="books_unread",
                ),
                path(
                    "unowned/",
                    views.book.UnownedIndexView.as_view(),
                    name="books_unowned",
                ),
                path(
                    "unowned/<int:page>/",
                    views.book.UnownedIndexView.as_view(),
                    name="books_unowned",
                ),
                path(
                    "unowned/<str:format>/",
                    views.book.UnownedIndexView.as_view(),
                    name="books_unowned",
                ),
                path(
                    "unowned/<str:format>/<int:page>/",
                    views.book.UnownedIndexView.as_view(),
                    name="books_unowned",
                ),
                path(
                    "<str:format>/", views.book.IndexView.as_view(), name="books_all",
                ),
            ]
        ),
    ),
    path("search/", views.basic_search, name="basic_search"),
    path("series/", views.series_list, name="series_index"),
    path(
        "series/<path:series>/",
        views.book.SeriesIndexView.as_view(),
        name="series_details",
    ),
    path("stats/", views.stats, name="stats"),
    path("tag/<str:tag_name>/", views.book.TagIndexView.as_view(), name="tag_details"),
    path("tags/", views.tag_cloud, name="tag_cloud"),
    path("report/", views.report, name="report"),
    path("report/<int:page>/", views.report, name="report"),
]
