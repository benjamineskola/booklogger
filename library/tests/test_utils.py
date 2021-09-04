import pytest

from library import utils


class TestUtils:
    def test_isbn_to_isbn10(self):
        assert utils.isbn_to_isbn10("9780306406157") == "0306406152"

    def test_isbn10_to_isbn(self):
        assert utils.isbn10_to_isbn("0306406152") == "9780306406157"

    def test_isbn10_to_isbn_invalid1(self):
        assert utils.isbn10_to_isbn("X030646152") == ""

    def test_isbn10_to_isbn_invalid2(self):
        assert utils.isbn10_to_isbn("030640615Z") == ""

    def test_round_trunc(self):
        import math

        assert utils.round_trunc(math.pi) == "3.14"
        assert utils.round_trunc(math.pi, 3) == "3.142"
        assert utils.round_trunc(math.pi, 5) == "3.14159"
        assert utils.round_trunc(0) == "0"

    def test_str2bool(self):
        assert utils.str2bool("0") is False
        assert utils.str2bool("1") is True
        assert utils.str2bool("2") is True
        assert utils.str2bool("yes") is True
        assert utils.str2bool("Yes") is True
        assert utils.str2bool("YES") is True
        assert utils.str2bool("true") is True
        assert utils.str2bool("True") is True
        assert utils.str2bool("TRUE") is True
        assert utils.str2bool("y") is True
        assert utils.str2bool("Y") is True
        assert utils.str2bool("t") is True
        assert utils.str2bool("T") is True

        assert utils.str2bool("no") is False
        assert utils.str2bool("No") is False
        assert utils.str2bool("NO") is False
        assert utils.str2bool("false") is False
        assert utils.str2bool("False") is False
        assert utils.str2bool("FALSE") is False
        assert utils.str2bool("n") is False
        assert utils.str2bool("N") is False
        assert utils.str2bool("f") is False
        assert utils.str2bool("F") is False

        with pytest.raises(ValueError):
            utils.str2bool("any other string")
