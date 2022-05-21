import pytest

from library.models import Tag


@pytest.mark.django_db
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

    def test_books_recursive(self, book_factory, tag_factory):
        tag1 = tag_factory()
        tag2 = tag_factory()
        tag3 = tag_factory()
        tag1.children.add(tag2)
        tag2.children.add(tag3)

        book = book_factory(tags=[tag3.name])
        assert book in tag1.books_recursive

    def test_related(self, book_factory, tag_factory):
        tag1 = tag_factory()
        tag2 = tag_factory()
        tag3 = tag_factory()
        book_factory(tags=[tag1.name, tag2.name])

        assert tag1 in tag2.related
        assert tag2 in tag1.related
        assert tag3 not in tag1.related
        assert tag1 not in tag3.related

    def test_sortable(self, tag_factory):
        tag1 = tag_factory(name="a")
        tag2 = tag_factory(name="b")

        assert tag1 < tag2

    def test_rename(self, book_factory, tag_factory):
        tag1 = tag_factory(name="foo")
        tag2 = tag_factory()
        tag1.parents.add(tag2)
        book = book_factory(tags=[tag1.name])

        assert "foo" in book.tags
        assert "bar" not in book.tags
        tag1.rename("bar")
        book.refresh_from_db()
        assert "foo" not in book.tags
        assert "bar" in book.tags

        assert tag2.children.first().name == "bar"

    def test_books_uniquely_tagged(self, book_factory, tag_factory):
        book1 = book_factory(tags=["foo"])
        book2 = book_factory(tags=["foo", "bar"])

        tag = Tag.objects["foo"]
        assert book1 in tag.books_uniquely_tagged
        assert book2 not in tag.books_uniquely_tagged

    def test_tags_case_insensitive(self, book_factory, tag_factory):
        book_factory(tags=["foo"])
        book_factory(tags=["Foo"])

        assert Tag.objects["foo"] == Tag.objects["Foo"]
