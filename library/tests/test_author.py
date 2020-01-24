import pytest

from library.factories import *
from library.models import *


class TestAuthor:
    @pytest.fixture
    def author(self, author_factory):
        return author_factory(surname="Smithee")

    def test_author_str(self, author):
        author.forenames = "Alan"
        assert str(author) == "Smithee, A."

    def test_author_initials_multi_names(self, author):
        author.forenames = "Alan Allen"
        assert str(author) == "Smithee, A.A."

    def test_author_initials_middle_initial(self, author):
        author.forenames = "Alan A."
        assert str(author) == "Smithee, A.A."

    def test_author_initials_middle_initial_multi(self, author):
        author.forenames = "Alan A.A."
        assert str(author) == "Smithee, A.A.A."

    def test_author_initials_all_initials_1(self, author):
        author.forenames = "A."
        assert str(author) == "Smithee, A."

    def test_author_initials_all_initials_2(self, author):
        author.forenames = "A.A."
        assert str(author) == "Smithee, A.A."
