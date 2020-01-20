from django.db.models.functions import Lower
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader

from .models import Author, Book, BookAuthor

# Create your views here.


def index(request):
    return HttpResponse("Hello, world. You're at the library index.")


def books_index(request):
    books = Book.objects.order_by(Lower("authors__surname"), "title")

    template = loader.get_template("books/index.html")
    context = {"books": books}
    return HttpResponse(template.render(context, request))


def author_details(request, author_id):
    try:
        author = Author.objects.get(pk=author_id)
    except Author.DoesNotExist:
        raise Http404("Author does not exist")
    return render(request, "authors/details.html", {"author": author})


def book_details(request, book_id):
    try:
        book = Book.objects.get(pk=book_id)
    except Book.DoesNotExist:
        raise Http404("Book does not exist")
    return render(request, "books/details.html", {"book": book})
