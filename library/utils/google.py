#!/usr/bin/env python

from typing import Optional

import requests


def fetch(google_id: str = "", isbn: str = "") -> Optional[dict[str, str]]:
    if google_id:
        search_url = f"https://www.googleapis.com/books/v1/volumes/{google_id}"
    elif isbn:
        search_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    else:
        return {}

    try:
        data = requests.get(search_url).json()
    except requests.exceptions.ConnectionError:
        return None

    if "error" in data and data["error"]["status"] == "RESOURCE_EXHAUSTED":
        return None

    if "volumeInfo" in data:
        volume = data["volumeInfo"]
        google_id = ""
    elif "items" in data and data["items"]:
        volume = data["items"][0]["volumeInfo"]
        google_id = data["items"][0]["id"]
    else:
        return {}

    first_published = volume["publishedDate"].split("-")[0]
    return {
        "google_books_id": google_id,
        "publisher": volume["publisher"],
        "page_count": volume["pageCount"],
        "first_published": first_published if first_published.isnumeric() else "",
    }
