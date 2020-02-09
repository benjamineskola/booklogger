from django.urls import path

from . import views

urlpatterns = [
    path("", views.reading_books, name="index"),
    path("books", views.books_all, name="books_all"),
    path("books/owned", views.owned_books, name="owned_books"),
    path("books/unowned", views.unowned_books, name="unowned_books"),
    path("books/borrowed", views.borrowed_books, name="borrowed_books"),
    path("books/reading", views.reading_books, name="reading_books"),
    path("books/read", views.read_books, name="read_books"),
    path("books/read/<int:year>", views.read_books, name="read_books"),
    path("books/toread", views.unread_books, name="unread_books"),
    path("authors", views.author_list, name="author_list"),
    path("author/<int:author_id>", views.author_details, name="author_details"),
    path("book/<int:book_id>", views.book_details, name="book_details"),
    path("book/<int:book_id>/start", views.start_reading, name="book_start_reading"),
    path("book/<int:book_id>/finish", views.finish_reading, name="book_finish_reading"),
    path(
        "book/<int:book_id>/update", views.update_progress, name="book_update_progress"
    ),
    path("search", views.basic_search, name="basic_search"),
    path("tag/<str:tag_name>", views.tag_details, name="tag_details"),
    path("book/<int:book_id>/add_tags", views.book_add_tags, name="book_add_tags"),
    path("tags", views.tag_cloud, name="tag_cloud"),
]
