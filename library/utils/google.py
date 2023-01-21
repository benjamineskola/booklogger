from typing import TYPE_CHECKING

import requests
from django.conf import settings

if TYPE_CHECKING:
    from library.models import Book  # pragma: no cover


def update(book: "Book") -> bool:
    data = fetch(book.google_books_id, book.isbn)
    if data is not None:
        book.update(data)
        return True
    return False


def fetch(google_id: str = "", isbn: str = "") -> dict[str, str] | None:
    if not settings.GOODREADS_KEY:
        return {}

    if google_id:
        search_url = f"https://www.googleapis.com/books/v1/volumes/{google_id}"
    elif isbn:
        search_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    else:
        return {}

    try:
        data = requests.get(search_url, timeout=10).json()
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
        "publisher": volume["publisher"] if "publisher" in volume else "",
        "page_count": volume["pageCount"] if "pageCount" in volume else 0,
        "first_published": first_published if first_published.isnumeric() else "",
    }
