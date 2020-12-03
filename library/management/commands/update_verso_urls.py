import re
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db.models import Q

from library.models import Book


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, **options):
        books = Book.objects.filter(publisher="Verso").filter(
            Q(publisher_url="") | ~Q(image_url__contains="versobooks.com")
        )

        for book in books:
            print(f"processing {book}")
            title = re.sub(
                r"[^A-Za-z0-9 -]+",
                " ",
                book.edition_title if book.edition_title else book.title,
            )
            title, *subtitle = title.split(": ", 1)
            query = f"{book.first_author} {title}"

            if url := self.search(query):
                self.process(book, url)
            elif url := self.search(title):
                self.process(book, url)
            elif url := self.search(str(book.first_author)):
                self.process(book, url)
            else:
                print(f"can't find {book}")

    def search(self, query):
        search_url = f"https://www.versobooks.com/search?q={quote_plus(query)}"
        search_results_page = BeautifulSoup(
            requests.get(search_url).text, features="html.parser"
        )
        search_results = search_results_page.find_all(class_="book-card")
        if len(search_results) == 1:
            return "https://versobooks.com" + search_results[0].a["href"]

    def process(self, book, url):
        if not book.publisher_url:
            book.publisher_url = url

        if "versobooks.com" not in book.image_url:
            if image := self.get_image_url(url):
                book.image_url = image

        book.save()

    def get_image_url(self, url):
        page = BeautifulSoup(requests.get(url).text, features="html.parser")
        images = page.find_all(class_="edition-single--cover-image")
        if images:
            return images[-1].img["src"]
