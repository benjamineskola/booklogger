import os
import re
from typing import Any, Optional

import requests
import xmltodict


def find(query: str, author_name: str = "") -> Optional[dict[str, str]]:
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
    else:
        return None


def find_all(query: str) -> list[dict[str, str]]:
    try:
        search_url = f"https://www.goodreads.com/search/index.xml?key={os.environ['GOODREADS_KEY']}&q={query}"
    except KeyError:
        return []

    data = requests.get(search_url).text
    xml = xmltodict.parse(data, dict_constructor=dict)

    try:
        all_results = xml["GoodreadsResponse"]["search"]["results"]["work"]
    except KeyError:
        return []
    except TypeError:
        return []

    results: list[dict[str, Any]] = (
        [all_results] if "id" in all_results else all_results
    )

    results = [
        {
            "authors": [(result["best_book"]["author"]["name"], "")],
            "title": result["best_book"]["title"],
            "goodreads_id": result["best_book"]["id"]["#text"],
            "first_published": result["original_publication_year"].get("#text"),
            "image_url": result["best_book"]["image_url"]
            if "nophoto" not in result["best_book"]["image_url"]
            else "",
        }
        for result in results
        if result["best_book"]["author"]["name"]
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
