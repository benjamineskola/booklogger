import pytest


@pytest.mark.django_db
class TestTag:
    def test_tag_cloud(self, book_factory, client, tag_factory):
        tag_factory(name="fiction")
        base_tag = tag_factory(name="non-fiction")
        base_tag.children.add(tag_factory(name="history"))
        base_tag.children.add(tag_factory(name="politics"))
        base_tag.children.add(tag_factory(name="philosophy"))

        book_factory(tags_list=["history", "politics"])
        book_factory(tags_list=["history"])
        book_factory(tags_list=["philosophy"])

        resp = client.get("/tags/")
        tags = resp.context_data["tags"]

        assert tags["size"]["non-fiction"]["non-fiction"] == 3
        assert tags["size"]["non-fiction"]["history"] == 2
        assert tags["size"]["non-fiction"]["politics"] == 1
        assert tags["size"]["non-fiction"]["philosophy"] == 1
