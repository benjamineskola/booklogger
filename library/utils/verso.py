import re
from typing import TYPE_CHECKING
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from library.models import Book  # pragma: no cover


def update(book: "Book") -> "Book":
    if book.publisher != "Verso":
        return book
    if book.publisher_url and "://versobooks.com" in book.image_url:
        return book

    title = re.sub(
        r"[^A-Za-z0-9 -]+",
        " ",
        book.edition_title if book.edition_title else book.title,
    )
    title, *_ = title.split(": ", 1)

    url = (
        book.publisher_url
        if book.publisher_url
        else find_page([book.search_query, title, str(book.first_author)])
    )
    if url:
        book.update({"publisher_url": url, "image_url": scrape_image(url)})
    return book


def find_page(queries: list[str]) -> str:
    for query in queries:
        search_url = f"https://www.versobooks.com/search?q={quote_plus(query)}"
        search_results_page = BeautifulSoup(
            requests.get(search_url, timeout=10).text, features="html.parser"
        )
        search_results = search_results_page.find_all(class_="book-card")
        if len(search_results) == 1:
            return f"https://versobooks.com{search_results[0].a['href']}"

    return ""


def scrape_image(url: str) -> str:
    page = BeautifulSoup(requests.get(url, timeout=10).text, features="html.parser")
    images = page.find_all(class_="edition-single--cover-image")
    if images:
        return str(images[-1].img["src"])

    return ""
