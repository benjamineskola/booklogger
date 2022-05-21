import pytest


@pytest.mark.django_db
class TestAuthor:
    def test_author_list(self, author_factory, client):
        resp = client.get("/authors/")
        assert len(resp.context_data["object_list"]) == 0

        author = author_factory()

        resp = client.get("/authors/")
        assert len(resp.context_data["object_list"]) == 1
        assert author in resp.context_data["object_list"]

    def test_author_list_by_gender(self, author_factory, client):
        male = author_factory(gender=1)
        female = author_factory(gender=2)
        resp = client.get("/authors/")
        assert len(resp.context_data["object_list"]) == 2

        resp = client.get("/authors/", {"gender": "1"})
        assert len(resp.context_data["object_list"]) == 1
        assert male in resp.context_data["object_list"]
        assert female not in resp.context_data["object_list"]

        resp = client.get("/authors/", {"gender": "female"})
        assert len(resp.context_data["object_list"]) == 1
        assert female in resp.context_data["object_list"]
        assert male not in resp.context_data["object_list"]

    def test_author_list_by_race(self, author_factory, client):
        white = author_factory(poc=0)
        poc = author_factory(poc=1)
        resp = client.get("/authors/")
        assert len(resp.context_data["object_list"]) == 2

        resp = client.get("/authors/", {"poc": "false"})
        assert len(resp.context_data["object_list"]) == 1
        assert white in resp.context_data["object_list"]
        assert poc not in resp.context_data["object_list"]

        resp = client.get("/authors/", {"poc": "true"})
        assert len(resp.context_data["object_list"]) == 1
        assert poc in resp.context_data["object_list"]
        assert white not in resp.context_data["object_list"]

    def test_author_detail(self, author, client):
        resp = client.get(f"/author/{author.slug}/")
        assert str(author) in str(resp.content)

    def test_author_edit(self, author, admin_client):
        resp = admin_client.get(f"/author/{author.slug}/edit/")
        assert f"Editing {author}" in str(resp.content)

    def test_author_new(self, admin_client):
        resp = admin_client.get("/author/new/")
        assert "New author" in str(resp.content)
