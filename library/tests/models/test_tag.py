import pytest

from library.models import Tag


@pytest.mark.django_db()
class TestTag:
    def test_str(self, tag_factory):
        assert str(tag_factory(name="foo")) == "foo"

    def test_name(self, tag_factory):
        assert tag_factory(name="foo").name == "foo"

    def test_fullname_without_parents(self, tag_factory):
        assert tag_factory(name="foo").fullname == "foo"

    def test_fullname_with_parents(self, tag_factory):
        bar = tag_factory(name="bar")
        bar.parents.add(tag_factory(name="foo"))
        assert bar.fullname == "foo :: bar"

    def test_parents_children_recursive(self, tag_factory):
        tag1 = tag_factory()
        tag2 = tag_factory()
        tag3 = tag_factory()
        tag1.children.add(tag2)
        tag2.children.add(tag3)
        assert tag1 in tag3.parents_recursive
        assert tag3 in tag1.children_recursive

    def test_books_recursive(self, book, tag_factory):
        tag1 = tag_factory()
        tag2 = tag_factory()
        tag3 = tag_factory()
        tag1.children.add(tag2)
        tag2.children.add(tag3)

        book.tags.add(tag3)
        assert book in tag1.books_recursive

    def test_related(self, book, tag_factory):
        tag1 = tag_factory()
        tag2 = tag_factory()
        tag3 = tag_factory()
        book.tags.set((tag1, tag2))

        assert tag1 in tag2.related
        assert tag2 in tag1.related
        assert tag3 not in tag1.related
        assert tag1 not in tag3.related

    def test_sortable(self, tag_factory):
        tag1 = tag_factory(name="a")
        tag2 = tag_factory(name="b")

        assert tag1 < tag2

    def test_books_uniquely_tagged(self, book_factory, tag_factory):
        tag1 = tag_factory()
        tag2 = tag_factory()

        book1 = book_factory()
        book1.tags.add(tag1)
        book2 = book_factory()
        book2.tags.set((tag1, tag2))

        assert book1 in tag1.books_uniquely_tagged
        assert book2 not in tag1.books_uniquely_tagged

    def test_tags_case_insensitive(self, book_factory):
        book1 = book_factory()
        book1.tags.add(Tag.objects["foo"])
        book2 = book_factory()
        book2.tags.add(Tag.objects["Foo"])

        assert Tag.objects["foo"] == Tag.objects["Foo"]
