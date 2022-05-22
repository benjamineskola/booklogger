import factory
from django.contrib.auth.models import User

from library.models import Author, Book, Tag


class AuthorFactory(factory.django.DjangoModelFactory):  # type: ignore
    class Meta:
        model = Author

    surname = factory.Faker("last_name")
    forenames = factory.Faker("first_name")


class BookFactory(factory.django.DjangoModelFactory):  # type: ignore
    class Meta:
        model = Book

    title = factory.Faker("sentence", nb_words=4)
    edition_format = 1
    first_author = factory.SubFactory(AuthorFactory)
    isbn = factory.Faker("isbn13", separator="")


class TagFactory(factory.django.DjangoModelFactory):  # type: ignore
    class Meta:
        model = Tag

    name = factory.Faker("word")


class UserFactory(factory.django.DjangoModelFactory):  # type: ignore
    class Meta:
        model = User

    username = "ben"
