import pytest

from library.models import Book


@pytest.mark.django_db()
class TestModel:
    def test_not_equal_lookup(self, book_factory):
        book1 = book_factory()
        book2 = book_factory()

        queryset = Book.objects.filter(title__ne=book1.title)
        assert book1 not in queryset
        assert book2 in queryset
