import os
import re

import requests
from bs4 import BeautifulSoup


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
    try:
        search_url = f"https://www.goodreads.com/search/index.xml?key={os.environ['GOODREADS_KEY']}&q={query}"
    except KeyError:
        return []

    xml = BeautifulSoup(requests.get(search_url).text)

    all_results = xml.goodreadsresponse.search.results.find_all("work")
    if not all_results:
        return []

    results = [
        {
            "authors": [(result.best_book.author.find("name").text, "")],
            "title": result.best_book.title.text,
            "goodreads_id": result.best_book.id.text,
            "first_published": result.original_publication_year.text or 0,
            "image_url": result.best_book.image_url.text
            if "nophoto" not in result.best_book.image_url.text
            else "",
        }
        for result in all_results
        if result.best_book.author.find("name").text
        not in ["SparkNotes", "BookRags", "BookHabits", "Bright Summaries"]
    ]
    return results


def scrape_image(goodreads_id: str) -> str:
    goodreads_url = f"https://www.goodreads.com/book/show/{goodreads_id}"
    text = requests.get(goodreads_url).text
    meta_tag = re.search(r"<meta[^>]*og:image[^>]*>", text)
    if meta_tag:
        image_url = re.search(r"https://.*\.jpg", meta_tag[0])
        if image_url and ("nophoto" not in image_url[0]):
            return str(image_url[0])

    return ""
