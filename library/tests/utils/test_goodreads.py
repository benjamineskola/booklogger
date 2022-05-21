import os

import pytest

from library.utils import goodreads


class TestGoodreads:
    query = "9781844678761"

    @pytest.fixture
    def mock_goodreads(self, requests_mock):
        os.environ["GOODREADS_KEY"] = "TEST_FAKE"
        requests_mock.get(
            f"https://www.goodreads.com/search/index.xml?key=TEST_FAKE&q={self.query}",
            text=open("library/fixtures/marx.xml").read(),
        )

        requests_mock.get(
            f"https://www.goodreads.com/search/index.xml?key=TEST_FAKE&q={self.query}_scrape",
            text=open("library/fixtures/marx_scrape.xml").read(),
        )

        requests_mock.get(
            "https://www.goodreads.com/book/show/13403951",
            text="<meta content='https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1373999264i/13403951._UY630_SR1200,630_.jpg' property='og:image'>",
        )

    @classmethod
    def teardown_class(cls):
        del os.environ["GOODREADS_KEY"]

    def test_find(self, mock_goodreads):
        result = goodreads.find(self.query)
        assert result["authors"] == [(("Karl Marx", ""))]
        assert "gr-assets" in result["image_url"]

    def test_find_with_author_name(self, mock_goodreads):
        result = goodreads.find("9781844678761", "Marx")
        assert result["authors"] == [("Karl Marx", "")]
        assert "gr-assets" in result["image_url"]

    def test_find_excluding_author_name(self, mock_goodreads):
        result = goodreads.find("9781844678761", "Engels")
        assert not result

    def test_find_and_scrape(self, mock_goodreads):
        result = goodreads.find(self.query + "_scrape")
        assert result["authors"] == [("Karl Marx", "")]
        assert "gr-assets" in result["image_url"]

    def test_failed_scrape(self, requests_mock, mock_goodreads):
        requests_mock.get(
            "https://www.goodreads.com/book/show/13403951",
            text="",
        )
        result = goodreads.find(self.query + "_scrape")
        assert result["authors"] == [("Karl Marx", "")]
        assert not result["image_url"]
