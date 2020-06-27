from django.urls import include, path

from . import views

app_name = "library"
urlpatterns = [
    path("", views.book.CurrentlyReadingView.as_view(), name="index"),
    path("author/<int:pk>", views.author.DetailView.as_view(), name="author_details"),
    path("authors", views.author.IndexView.as_view(), name="author_list"),
    path(
        "book/<int:pk>/",
        include(
            [
                path("", views.book.DetailView.as_view(), name="book_details"),
                path("add_tags", views.book.add_tags, name="book_add_tags",),
                path("finish", views.book.finish_reading, name="book_finish_reading",),
                path("start", views.book.start_reading, name="book_start_reading",),
                path(
                    "update", views.book.update_progress, name="book_update_progress",
                ),
            ]
        ),
    ),
    path("book/import/<str:query>", views.import_book, name="book_import"),
    path(
        "books/",
        include(
            [
                path("", views.book.IndexView.as_view(), name="books_all"),
                path(
                    "borrowed",
                    views.book.BorrowedIndexView.as_view(),
                    name="books_borrowed",
                ),
                path("owned", views.book.OwnedIndexView.as_view(), name="books_owned"),
                path(
                    "owned/bydate",
                    views.book.OwnedByDateView.as_view(),
                    name="books_owned_by_date",
                ),
                path(
                    "owned/<str:format>",
                    views.book.OwnedIndexView.as_view(),
                    name="books_owned",
                ),
                path("read", views.book.ReadView.as_view(), name="books_read"),
                path(
                    "read/<int:year>", views.book.ReadView.as_view(), name="books_read"
                ),
                path(
                    "reading",
                    views.book.CurrentlyReadingView.as_view(),
                    name="books_currently_reading",
                ),
                path(
                    "toread", views.book.UnreadIndexView.as_view(), name="books_unread"
                ),
                path(
                    "toread/<str:format>",
                    views.book.UnreadIndexView.as_view(),
                    name="books_unread",
                ),
                path(
                    "unowned",
                    views.book.UnownedIndexView.as_view(),
                    name="books_unowned",
                ),
            ]
        ),
    ),
    path("search", views.basic_search, name="basic_search"),
    path("stats", views.stats, name="stats"),
    path("tag/<str:tag_name>", views.tag_details, name="tag_details"),
    path("tags", views.tag_cloud, name="tag_cloud"),
]
