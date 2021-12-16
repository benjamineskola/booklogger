from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup


def find_page(queries: list[str]) -> str:
    for query in queries:
        search_url = f"https://www.versobooks.com/search?q={quote_plus(query)}"
        search_results_page = BeautifulSoup(
            requests.get(search_url).text, features="html.parser"
        )
        search_results = search_results_page.find_all(class_="book-card")
        if len(search_results) == 1:
            return f"https://versobooks.com{search_results[0].a['href']}"

    return ""


def scrape_image(url: str) -> str:
    page = BeautifulSoup(requests.get(url).text, features="html.parser")
    images = page.find_all(class_="edition-single--cover-image")
    if images:
        return str(images[-1].img["src"])

    return ""
