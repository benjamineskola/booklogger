from math import pi

import pytest

from library import utils


class TestUtils:
    @pytest.mark.parametrize(
        ("isbn10", "isbn13"),
        [
            ("0140135154", "9780140135152"),
            ("014103579X", "9780141035796"),
        ],
    )
    def test_isbn_to_isbn10_and_back(self, isbn10, isbn13):
        assert utils.isbn_to_isbn10(isbn13) == isbn10
        assert utils.isbn10_to_isbn(isbn10) == isbn13

    @pytest.mark.parametrize(
        "isbn",
        [
            "796",
            "",
            "not an isbn",
            "978014103579X",
            "Z141035790",
            "Z14103579X",
            "014103579Z",
        ],
    )
    def test_invalid_isbn(self, isbn):
        assert not utils.isbn_to_isbn10(isbn)
        assert not utils.isbn10_to_isbn(isbn)

    def test_isbn13_treated_as_isbn10(self):
        assert utils.isbn10_to_isbn("9780141035796") == "9780141035796"

    def test_sbn_to_isbn13(self):
        assert utils.isbn10_to_isbn("140135154") == "9780140135152"

        # when converted back it'll prepend a 0: isbn format not sbn
        assert utils.isbn_to_isbn10("9780140135152") == "0140135154"

    def test_isbn10_to_isbn_with_invalid_check_digit(self):
        assert utils.isbn10_to_isbn("0140135151") == "9780140135152"

        # converting back gives correct check digit
        assert utils.isbn_to_isbn10("9780140135152") == "0140135154"

    @pytest.mark.parametrize(
        ("test_input", "expected"),
        [
            ((pi,), "3.14"),
            ((pi, 2), "3.14"),
            ((pi, 3), "3.142"),
            ((pi, 5), "3.14159"),
            ((0,), "0"),
            (("not a number",), "??"),
        ],
    )
    def test_round_trunc(self, test_input, expected):
        assert utils.round_trunc(*test_input) == expected

    @pytest.mark.parametrize(
        ("test_input", "expected"),
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
        with pytest.raises(ValueError):  # noqa: PT011
            utils.str2bool("any other string")

    @pytest.mark.parametrize(
        ("test_input", "expected"),
        [
            ([], []),
            ([[]], []),
            ([[], []], []),
            ([[1]], [1]),
            ([[1], [2]], [1, 2]),
            ([[1], ["2"]], [1, "2"]),
            ([["1"], ["2"]], ["1", "2"]),
            ([[1, 2], [3, 4]], [1, 2, 3, 4]),
            ([[1, "2"], [3, "4"]], [1, "2", 3, "4"]),
            ([[1, 2], [3], [4]], [1, 2, 3, 4]),
            ([[1, 2], [3], [4], []], [1, 2, 3, 4]),
        ],
    )
    def test_flatten(self, test_input, expected):
        assert utils.flatten(test_input) == expected
