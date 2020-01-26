from django.urls import path

from . import views

urlpatterns = [
    path("", views.books_index, name="books"),
    path("owned", views.owned_books, name="owned_books"),
    path("unowned", views.unowned_books, name="unowned_books"),
    path("borrowed", views.borrowed_books, name="borrowed_books"),
    path("read", views.read_books, name="read_books"),
    path("toread", views.unread_books, name="unread_books"),
    path("authors", views.all_authors, name="all_authors"),
    path("author/<int:author_id>", views.author_details, name="author_details"),
    path("book/<int:book_id>", views.book_details, name="book_details"),
]
