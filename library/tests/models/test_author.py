import pytest

from library.factories import *
from library.models import *


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
