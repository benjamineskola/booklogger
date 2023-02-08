from pathlib import Path

import pytest

from library.utils import goodreads


class TestGoodreads:
    query = "9781844678761"

    @pytest.fixture()
    def _mock_goodreads(self, requests_mock, _goodreads_key):
        with Path("library/fixtures/marx.xml").open() as fixture:
            requests_mock.get(
                f"https://www.goodreads.com/search/index.xml?key=TEST_FAKE&q={self.query}",
                text=fixture.read(),
            )

        with Path("library/fixtures/marx_scrape.xml").open() as fixture:
            requests_mock.get(
                f"https://www.goodreads.com/search/index.xml?key=TEST_FAKE&q={self.query}_scrape",
                text=fixture.read(),
            )

        requests_mock.get(
            "https://www.goodreads.com/book/show/13403951",
            text="<meta content='https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1373999264i/13403951._UY630_SR1200,630_.jpg' property='og:image'>",
        )

    @pytest.mark.usefixtures("_mock_goodreads")
    def test_find(self):
        result = goodreads.find(self.query)
        assert result["authors"] == [(("Karl Marx", ""))]
        assert "gr-assets" in result["image_url"]

    @pytest.mark.usefixtures("_mock_goodreads")
    def test_find_with_author_name(self):
        result = goodreads.find("9781844678761", "Marx")
        assert result["authors"] == [("Karl Marx", "")]
        assert "gr-assets" in result["image_url"]

    @pytest.mark.usefixtures("_mock_goodreads")
    def test_find_excluding_author_name(self):
        result = goodreads.find("9781844678761", "Engels")
        assert not result

    @pytest.mark.usefixtures("_mock_goodreads")
    def test_find_and_scrape(self):
        result = goodreads.find(self.query + "_scrape")
        assert result["authors"] == [("Karl Marx", "")]
        assert "gr-assets" in result["image_url"]

    @pytest.mark.usefixtures("_mock_goodreads")
    def test_failed_scrape(self, requests_mock):
        requests_mock.get(
            "https://www.goodreads.com/book/show/13403951",
            text="",
        )
        result = goodreads.find(self.query + "_scrape")
        assert result["authors"] == [("Karl Marx", "")]
        assert not result["image_url"]

    @pytest.mark.usefixtures("_goodreads_key")
    def test_no_result(self, requests_mock):
        query = "something ridiculous and nonexistent"
        requests_mock.get(
            f"https://www.goodreads.com/search/index.xml?key=TEST_FAKE&q={query}",
            text='<?xml version="1.0" encoding="UTF-8"?>\n<GoodreadsResponse><search><results></results></search></GoodreadsResponse>',
        )
        result = goodreads.find(query)
        assert not result
