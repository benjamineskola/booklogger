from django.urls import include, path

from . import views

app_name = "library"
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
                path("borrowed", views.book.borrowed, name="books_borrowed"),
                path("owned", views.book.owned, name="books_owned"),
                path(
                    "owned/bydate",
                    views.book.owned_by_date,
                    name="books_owned_by_date",
                ),
                path("read", views.book.read, name="books_read"),
                path("read/<int:year>", views.book.read, name="books_read"),
                path(
                    "reading",
                    views.book.currently_reading,
                    name="books_currently_reading",
                ),
                path("toread", views.book.unread, name="books_unread"),
                path("unowned", views.book.unowned, name="books_unowned"),
            ]
        ),
    ),
    path("search", views.basic_search, name="basic_search"),
    path("stats", views.stats, name="stats"),
    path("tag/<str:tag_name>", views.tag_details, name="tag_details"),
    path("tags", views.tag_cloud, name="tag_cloud"),
]
