#!/usr/bin/env python

import os
import re
from typing import Any, Optional

import requests
import xmltodict


def find(query: str, author_name: str = "") -> Optional[dict[str, Any]]:
    results = find_all(query)
    if author_name:
        results = [
            result
            for result in results
            if author_name.lower() in result["best_book"]["author"]["name"].lower()
        ]
    if results:
        return results[0]
    else:
        return None


def find_all(query: str) -> list[dict[str, Any]]:
    search_url = f"https://www.goodreads.com/search/index.xml?key={os.environ['GOODREADS_KEY']}&q={query}"
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
        dict(**result.pop("best_book"), **result)
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
