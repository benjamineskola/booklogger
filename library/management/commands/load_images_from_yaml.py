#!/usr/bin/env python3
import datetime
import re
import sys

import yaml
from django.core.management.base import BaseCommand

from library.models import Author, Book, BookAuthor, LogEntry


class Command(BaseCommand):
    def _normalize(self, raw_name):
        words = raw_name.split(" ")
        surname = words.pop()

        while words and words[-1].lower() in ["von", "van", "der", "le", "de"]:
            surname = words.pop() + " " + surname

        forenames = " ".join(words)
        return (surname.strip(), forenames.strip())

    def add_arguments(self, parser):
        parser.add_argument("file", nargs="?")
        parser.add_argument("-f", "--force", action="store_true", default=False)

    def handle(self, **options):
        self.processed_entries = []
        if options["file"]:
            input_data = open(options["file"]).read()
        else:
            input_data = sys.stdin.read()
        data = yaml.safe_load(input_data)

        for book_data in data:
            print(book_data)
            try:
                book = Book.objects.get(**book_data["ids"])
            except:
                continue
            book.image_url = book_data["image_url"]
            book.save()
