#!/usr/bin/env python3
import datetime
import re
import sys

import yaml
from django.core.management.base import BaseCommand

from library.models import Author, Book, BookAuthor, LogEntry


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("file", nargs="?")
        parser.add_argument("-f", "--force", action="store_true", default=False)

    def handle(self, **options):
        self.processed_entries = []
        if options["file"]:
            input_data = open(options["file"]).readlines()[1:]
        else:
            input_data = sys.stdin.readlines()[1:]

        for line in input_data:
            title, author, *ids = line.strip().split("\t")

            if not ids:
                continue

            author_split = Author.normalise_name(author)
            surname = author_split["surname"]
            forenames = author.split["forenames"]

            title = re.sub(r"^_(.*)_\s*$", r"\1", title)
            if title.endswith(")"):
                title = title.split(" (")[0]

            books = Book.objects.filter(title=title, authors__surname=surname)
            if books.count() == 0:
                print(f"no such book {title} by {surname}?")
                authors = Author.objects.filter(surname=surname, forenames=forenames)
                if authors.count() > 1:
                    print("need to be more specific about {authors}")
                elif authors.count() == 0:
                    print(f"need to create {surname}, {forenames}")
                    authors = [Author(surname=surname, forenames=forenames)]
                    authors[0].save()
                else:
                    print(f"can use {surname}, {forenames}")
                    book = Book(title=title, first_author=authors[0])
                    book.save()
            elif books.count() > 1:
                print(f"more than one book matches {title}")
            else:
                book = books[0]

            interesting_id = ids[-1]
            if interesting_id.startswith("978"):
                if book.isbn and book.isbn != interesting_id:
                    print(f"{book} has different isbns")
                else:
                    book.isbn = interesting_id
                    book.save()
            elif interesting_id.startswith("A") or interesting_id.startswith("B"):
                if book.asin and book.asin != interesting_id:
                    print(f"{book} has different asins")
                else:
                    book.asin = interesting_id
                    book.save()
            else:
                print(interesting_id)
