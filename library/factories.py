import factory
from django.contrib.auth.models import User
from pytest_factoryboy import register

from library.models import Author, Book, BookAuthor


class AuthorFactory(factory.Factory):  # type: ignore
    class Meta:
        model = Author

    surname = factory.Faker("last_name")
    forenames = factory.Faker("first_name")


class BookFactory(factory.Factory):  # type: ignore
    class Meta:
        model = Book

    title = factory.Faker("sentence", nb_words=4)


class BookAuthorFactory(factory.Factory):  # type: ignore
    class Meta:
        model = BookAuthor


class UserFactory(factory.Factory):  # type: ignore
    class Meta:
        model = User


register(AuthorFactory)
register(BookFactory)
register(BookAuthorFactory)
register(UserFactory)
