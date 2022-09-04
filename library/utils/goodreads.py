from typing import TYPE_CHECKING

import requests
from bs4 import BeautifulSoup
from django.conf import settings

if TYPE_CHECKING:
    from library.models import Book  # pragma: no cover


def update(book: "Book") -> "Book":
    result: dict[str, str] | None = {}
    for query in [book.asin, book.isbn, book.search_query]:
        if query and (
            result := find(
                query, book.first_author.surname if book.first_author else ""
            )
        ):
            book.update(result)
            break

    return book


def find(query: str, author_name: str = "") -> dict[str, str] | None:
    results = find_all(query)
    if author_name:
        results = [
            result
            for result in results
            if author_name.lower() in result["authors"][0][0].lower()
        ]
    if results:
        result = results[0]
        if not result["image_url"]:
            result["image_url"] = scrape_image(result["goodreads_id"])
        return result

    return None


def find_all(query: str) -> list[dict[str, str]]:
    if not settings.GOODREADS_KEY:
        return []

    search_url = f"https://www.goodreads.com/search/index.xml?key={settings.GOODREADS_KEY}&q={query}"

    xml = BeautifulSoup(requests.get(search_url).text, features="xml")

    all_results = xml.GoodreadsResponse.search.results.find_all("work")
    if not all_results:
        return []

    results = [
        {
            "authors": [(result.best_book.author.find("name").text, "")],
            "title": result.best_book.title.text,
            "goodreads_id": result.best_book.id.text,
            "first_published": result.original_publication_year.text or 0,
            "image_url": result.best_book.image_url.text
            if (
                "nophoto" not in result.best_book.image_url.text
                and "goodreads_wide" not in result.best_book.image_url.text
            )
            else "",
        }
        for result in all_results
        if result.best_book.author.find("name").text
        not in ["SparkNotes", "BookRags", "BookHabits", "Bright Summaries"]
    ]
    return results


def scrape_image(goodreads_id: str) -> str:
    goodreads_url = f"https://www.goodreads.com/book/show/{goodreads_id}"
    data = BeautifulSoup(requests.get(goodreads_url).text, features="lxml")
    if meta_tag := data.find(
        "meta", property="og:image", content=lambda x: "nophoto" not in x
    ):
        return str(meta_tag.get("content"))

    return ""
