import factory
from pytest_factoryboy import register

from library.models import Author, Book, BookAuthor


class AuthorFactory(factory.Factory):
    class Meta:
        model = Author


class BookFactory(factory.Factory):
    class Meta:
        model = Book


class BookAuthorFactory(factory.Factory):
    class Meta:
        model = BookAuthor


register(AuthorFactory)
register(BookFactory)
register(BookAuthorFactory)
