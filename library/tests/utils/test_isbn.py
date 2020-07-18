from library.utils import isbn10_to_isbn, isbn_to_isbn10


class TestISBN:
    def test_isbn_to_isbn10(self):
        assert isbn_to_isbn10("9780140135152") == "0140135154"
        assert isbn_to_isbn10("9780141035796") == "014103579X"

    def test_isbn_to_isbn10_invalid_input(self):
        assert isbn_to_isbn10("796") == ""
        assert isbn_to_isbn10("") == ""
        assert isbn_to_isbn10("not an isbn") == ""
        assert isbn_to_isbn10("978014103579X") == ""

    def test_isbn10_to_isbn(self):
        assert isbn10_to_isbn("0140135154") == "9780140135152"
        assert isbn10_to_isbn("014103579X") == "9780141035796"
        assert isbn10_to_isbn("9780141035796") == "9780141035796"

    def test_isbn10_to_isbn_invalid_input(self):
        assert isbn10_to_isbn("796") == ""
        assert isbn10_to_isbn("") == ""
        assert isbn10_to_isbn("not an isbn") == ""
        assert isbn10_to_isbn("978014103579X") == ""

    def test_sbn_to_isbn13(self):
        assert isbn10_to_isbn("140135154") == "9780140135152"

    def test_isbn10_to_isbn_with_invalid_check_digit(self):
        assert isbn10_to_isbn("0140135151") == "9780140135152"
