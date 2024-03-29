import factory
import faker
from django.contrib.auth.models import User

from library.models import Author, Book, Tag

fake = faker.Faker()


class AuthorFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = Author

    surname = factory.Faker("last_name")
    forenames = factory.Faker("first_name")


class BookFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = Book

    title = factory.Faker("sentence", nb_words=4)
    edition_format = 1
    first_author = factory.SubFactory(AuthorFactory)
    isbn = factory.Faker("isbn13", separator="")


class TagFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = Tag

    name = factory.LazyAttribute(lambda _: fake.unique.word())


class UserFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = User

    username = "ben"
