from math import pi

import pytest

from library import utils


class TestUtils:
    @pytest.mark.parametrize(
        "isbn10,isbn13",
        [
            ("0306406152", "9780306406157"),
            ("178067905X", "9781780679051"),
        ],
    )
    def test_isbn_to_isbn10_and_back(self, isbn10, isbn13):
        assert utils.isbn_to_isbn10(isbn13) == isbn10
        assert utils.isbn10_to_isbn(isbn10) == isbn13

    @pytest.mark.parametrize(
        "isbn",
        [
            "X030646152",
            "030640615Z",
        ],
    )
    def test_isbn10_to_isbn_invalid(self, isbn):
        assert utils.isbn10_to_isbn(isbn) == ""

    @pytest.mark.parametrize(
        "test_input,expected",
        [
            ((pi,), "3.14"),
            ((pi, 2), "3.14"),
            ((pi, 3), "3.142"),
            ((pi, 5), "3.14159"),
            ((0,), "0"),
        ],
    )
    def test_round_trunc(self, test_input, expected):
        assert utils.round_trunc(*test_input) == expected

    @pytest.mark.parametrize(
        "test_input,expected",
        [
            ("0", False),
            ("0", False),
            ("1", True),
            ("2", True),
            ("yes", True),
            ("Yes", True),
            ("YES", True),
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("y", True),
            ("Y", True),
            ("t", True),
            ("T", True),
            ("no", False),
            ("No", False),
            ("NO", False),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("n", False),
            ("N", False),
            ("f", False),
            ("F", False),
        ],
    )
    def test_str2bool(self, test_input, expected):
        assert utils.str2bool(test_input) is expected

    def test_str2bool_invalid_input(self):
        with pytest.raises(ValueError):
            utils.str2bool("any other string")
