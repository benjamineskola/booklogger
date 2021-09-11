import pytest

from library.models import Author


class TestAuthor:
    @pytest.fixture
    def author(self, author_factory):
        return author_factory(surname="Smithee")

    def test_author_str(self, author):
        author.forenames = "Alan"
        assert author.initials == "A."
        assert str(author) == "Alan Smithee"

    def test_author_initials_multi_names(self, author):
        author.forenames = "Alan Allen"
        assert author.initials == "A.A."
        assert str(author) == "Alan Allen Smithee"

    def test_author_initials_middle_initial(self, author):
        author.forenames = "Alan A."
        assert author.initials == "A.A."
        assert str(author) == "Alan A. Smithee"

    def test_author_initials_middle_initial_multi(self, author):
        author.forenames = "Alan A.A."
        assert author.initials == "A.A.A."
        assert str(author) == "Alan A.A. Smithee"

    def test_author_initials_all_initials_1(self, author):
        author.forenames = "A."
        assert author.initials == "A."
        assert str(author) == "A. Smithee"

    def test_author_initials_all_initials_2(self, author):
        author.forenames = "A.A."
        assert author.initials == "A.A."
        assert str(author) == "A.A. Smithee"

    def test_author_preferred_name(self):
        author = Author(
            surname="Tolkien",
            forenames="John Ronald Reuel",
            preferred_forenames="J.R.R.",
        )
        assert author.initials == "J.R.R."
        assert str(author) == "J.R.R. Tolkien"
        assert author.full_name == "John Ronald Reuel Tolkien"
        assert author.name_with_initials == "Tolkien, J.R.R."

    def test_author_get_by_all_names(self, transactional_db):
        author = Author(
            surname="Tolkien",
            forenames="John Ronald Reuel",
            preferred_forenames="J.R.R.",
        )
        author.save()
        assert Author.objects.get_by_single_name("J.R.R. Tolkien") == author
        assert Author.objects.get_by_single_name("J. R. R. Tolkien") == author
        assert Author.objects.get_by_single_name("John Ronald Reuel Tolkien") == author

    def test_author_get_by_single_name(self, author, transactional_db):
        author.forenames = "Alan"
        author.save()
        assert Author.objects.get_by_single_name("Alan Smithee") == author

    def test_author_get_by_single_name_organisation(self, transactional_db):
        author = Author(surname="Smithee Books")
        author.save()
        assert Author.objects.get_by_single_name("Smithee Books") == author
