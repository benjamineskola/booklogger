import pytest

from library.models import *


class TestAuthor:
    @pytest.fixture
    def author(self):
        return Author(surname="Smithee")

    def test_author_str(self, author):
        # author = Author(surname="Smithee", forenames="Alan")
        author.forenames = "Alan"
        assert str(author) == "Smithee, A."

    def test_author_initials_multi_names(self, author):
        # author = Author(surname="Smithee", forenames="Alan Allen")
        author.forenames = "Alan Allen"
        assert str(author) == "Smithee, A.A."

    def test_author_initials_middle_initial(self, author):
        # author = Author(surname="Smithee", forenames="Alan A.")
        author.forenames = "Alan A."
        assert str(author) == "Smithee, A.A."

    def test_author_initials_middle_initial_multi(self, author):
        # author = Author(surname="Smithee", forenames="Alan A.A.")
        author.forenames = "Alan A.A."
        assert str(author) == "Smithee, A.A.A."

    def test_author_initials_all_initials_1(self, author):
        # author = Author(surname="Smithee", forenames="A.")
        author.forenames = "A."
        assert str(author) == "Smithee, A."

    def test_author_initials_all_initials_2(self, author):
        # author = Author(surname="Smithee", forenames="A.A.")
        author.forenames = "A.A."
        assert str(author) == "Smithee, A.A."
