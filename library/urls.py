from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.book.currently_reading, name="index"),
    path("author/<int:author_id>", views.author_details, name="author_details"),
    path("authors", views.author_list, name="author_list"),
    path(
        "book/",
        include(
            [
                path("<int:book_id>", views.book.details, name="book_details"),
                path(
                    "<int:book_id>/add_tags", views.book.add_tags, name="book_add_tags",
                ),
                path(
                    "<int:book_id>/finish",
                    views.book.finish_reading,
                    name="book_finish_reading",
                ),
                path(
                    "<int:book_id>/start",
                    views.book.start_reading,
                    name="book_start_reading",
                ),
                path(
                    "<int:book_id>/update",
                    views.book.update_progress,
                    name="book_update_progress",
                ),
            ]
        ),
    ),
    path(
        "books/",
        include(
            [
                path("", views.book.all, name="books_all"),
                path("borrowed", views.book.borrowed, name="borrowed_books"),
                path("owned", views.book.owned, name="owned_books"),
                path(
                    "owned/bydate",
                    views.book.owned_by_date,
                    name="owned_books_by_date",
                ),
                path("read", views.book.read, name="read_books"),
                path("read/<int:year>", views.book.read, name="read_books"),
                path("reading", views.book.currently_reading, name="reading_books"),
                path("toread", views.book.unread, name="unread_books"),
                path("unowned", views.book.unowned, name="unowned_books"),
            ]
        ),
    ),
    path("search", views.basic_search, name="basic_search"),
    path("stats", views.stats, name="stats"),
    path("tag/<str:tag_name>", views.tag_details, name="tag_details"),
    path("tags", views.tag_cloud, name="tag_cloud"),
]
