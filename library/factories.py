import factory
from django.contrib.auth.models import User

from library.models import Author, Book


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


class UserFactory(factory.django.DjangoModelFactory):  # type: ignore
    class Meta:
        model = User

    username = "ben"
