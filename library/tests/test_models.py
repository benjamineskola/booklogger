import pytest

from library.factories import book_factory  # noqa: F401
from library.models import Book


@pytest.mark.django_db
class TestModel:
    def test_not_equal_lookup(self, book_factory):  # noqa: F811
        book1 = book_factory()
        book2 = book_factory()

        book1.save()
        book2.save()

        queryset = Book.objects.filter(title__ne=book1.title)
        assert book1 not in queryset
        assert book2 in queryset
