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
            text="""<?xml version="1.0" encoding="UTF-8"?>
<GoodreadsResponse>
  <Request>
    <authentication>true</authentication>
      <key><![CDATA[uQNpg76WDFI4sGANSqZKmQ]]></key>
    <method><![CDATA[search_index]]></method>
  </Request>
  <search>
  <query><![CDATA[9781844678761]]></query>
    <results-start>1</results-start>
    <results-end>1</results-end>
    <total-results>1</total-results>
    <source>Goodreads</source>
    <query-time-seconds>0.01</query-time-seconds>
    <results>
        <work>
  <id type="integer">2205479</id>
  <books_count type="integer">2367</books_count>
  <ratings_count type="integer">128092</ratings_count>
  <text_reviews_count type="integer">6663</text_reviews_count>
  <original_publication_year type="integer">1848</original_publication_year>
  <original_publication_month type="integer">2</original_publication_month>
  <original_publication_day type="integer">21</original_publication_day>
  <average_rating>3.61</average_rating>
  <best_book type="Book">
    <id type="integer">13403951</id>
    <title>The Communist Manifesto</title>
    <author>
      <id type="integer">7084</id>
      <name>Karl Marx</name>
    </author>
    <image_url>https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1373999264l/13403951._SX98_.jpg</image_url>
    <small_image_url>https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1373999264l/13403951._SX50_.jpg</small_image_url>
  </best_book>
</work>

    </results>
</search>

</GoodreadsResponse> """,
        )

        requests_mock.get(
            f"https://www.goodreads.com/search/index.xml?key=TEST_FAKE&q={self.query}_scrape",
            text="""<?xml version="1.0" encoding="UTF-8"?>
<GoodreadsResponse>
  <Request>
    <authentication>true</authentication>
      <key><![CDATA[uQNpg76WDFI4sGANSqZKmQ]]></key>
    <method><![CDATA[search_index]]></method>
  </Request>
  <search>
  <query><![CDATA[9781844678761]]></query>
    <results-start>1</results-start>
    <results-end>1</results-end>
    <total-results>1</total-results>
    <source>Goodreads</source>
    <query-time-seconds>0.01</query-time-seconds>
    <results>
        <work>
  <id type="integer">2205479</id>
  <books_count type="integer">2367</books_count>
  <ratings_count type="integer">128092</ratings_count>
  <text_reviews_count type="integer">6663</text_reviews_count>
  <original_publication_year type="integer">1848</original_publication_year>
  <original_publication_month type="integer">2</original_publication_month>
  <original_publication_day type="integer">21</original_publication_day>
  <average_rating>3.61</average_rating>
  <best_book type="Book">
    <id type="integer">13403951</id>
    <title>The Communist Manifesto</title>
    <author>
      <id type="integer">7084</id>
      <name>Karl Marx</name>
    </author>
    <image_url>https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1373999264l/nophoto.jpg</image_url>
    <small_image_url>https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1373999264l/nophoto.jpg</small_image_url>
  </best_book>
</work>

    </results>
</search>

</GoodreadsResponse> """,
        )

        requests_mock.get(
            "https://www.goodreads.com/book/show/13403951",
            text="<meta content='https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1373999264i/13403951._UY630_SR1200,630_.jpg' property='og:image'>",
        )

    def test_find(self, mock_goodreads):
        result = goodreads.find(self.query)
        assert result["authors"] == ["Karl Marx"]
        assert "gr-assets" in result["image_url"]

    def test_find_with_author_name(self, mock_goodreads):
        result = goodreads.find("9781844678761", "Marx")
        assert result["authors"] == ["Karl Marx"]
        assert "gr-assets" in result["image_url"]

    def test_find_excluding_author_name(self, mock_goodreads):
        result = goodreads.find("9781844678761", "Engels")
        assert not result

    def test_find_and_scrape(self, mock_goodreads):
        result = goodreads.find(self.query + "_scrape")
        assert result["authors"] == ["Karl Marx"]
        assert "gr-assets" in result["image_url"]

    def test_failed_scrape(self, requests_mock, mock_goodreads):
        requests_mock.get(
            "https://www.goodreads.com/book/show/13403951",
            text="",
        )
        result = goodreads.find(self.query + "_scrape")
        assert result["authors"] == ["Karl Marx"]
        assert not result["image_url"]
