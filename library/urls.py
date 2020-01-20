from django.urls import path

from . import views

urlpatterns = [
    path("", views.books_index, name="books"),
    path("author/<int:author_id>", views.author_details, name="details"),
    path("book/<int:book_id>", views.book_details, name="details"),
]
