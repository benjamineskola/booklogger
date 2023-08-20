import pytest

from library.models import Tag


@pytest.mark.django_db()
class TestTag:
    def test_tag_cloud(self, book_factory, client, tag_factory):
        base_tag = tag_factory(name="non-fiction")
        base_tag.children.add(tag_factory(name="history"))
        base_tag.children.add(tag_factory(name="politics"))
        base_tag.children.add(tag_factory(name="philosophy"))

        book1 = book_factory()
        book1.tags.set(
            (Tag.objects.get(name="history"), Tag.objects.get(name="politics"))
        )
        book2 = book_factory()
        book2.tags.set((Tag.objects.get(name="history"),))
        book3 = book_factory()
        book3.tags.set((Tag.objects.get(name="philosophy"),))

        resp = client.get("/tags/")
        tags = resp.context_data["tags"]

        assert tags["size"]["non-fiction"]["non-fiction"] == 3
        assert tags["size"]["non-fiction"]["history"] == 2
        assert tags["size"]["non-fiction"]["politics"] == 1
        assert tags["size"]["non-fiction"]["philosophy"] == 1
