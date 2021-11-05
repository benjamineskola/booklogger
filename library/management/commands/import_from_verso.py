import re
import sys

from django.core.management.base import BaseCommand

from library.models import Book
from library.utils import flatten, goodreads
from library.utils.goodreads_create import goodreads_create


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, **options):
        lines = [i.strip() for i in sys.stdin.readlines() if i.strip()]
        print(lines)
        for line in lines:
            title, _, isbn = line.rsplit(", ", 2)
            _, title = title.strip().split(" ", 1)
            title, *authors = re.split(r" (?:Edited )*?by ", title, 1)
            if authors:
                authors = flatten([author.split(" and ") for author in authors])

            try:
                book = Book.objects.get(title__istartswith=title.lower())
                print(f"found {title} in the database, skipping")

                if not book.owned:
                    book.isbn = isbn
                    book.edition_format = Book.Format.EBOOK
                    book.publisher = "Verso"
                    book.mark_owned()
                    book.save()
                elif (
                    book.edition_format != Book.Format.EBOOK
                    and not book.has_ebook_edition
                ):
                    # looks like a hard copy is already owned
                    book.ebook_isbn = isbn
                    book.has_ebook_edition = True
                    book.save()
                continue
            except Book.DoesNotExist:
                print(f"no book named {title} in the database, continuing")

            goodreads_book = goodreads.find(isbn)
            if goodreads_book:
                found_title, *_ = goodreads_book["title"].split(": ", 1)
                if found_title.lower() == title.lower():
                    print(f"found {title} on goodreads")
                    book = goodreads_create(data=goodreads_book)
                    book.isbn = isbn
                    book.edition_format = Book.Format.EBOOK
                    book.publisher = "Verso"
                    book.mark_owned()
                    book.save()
                else:
                    print(f"got {found_title} instead of {title}")
            else:
                print(f"could not find {title} by isbn")
                goodreads_book = goodreads.find(f"{title} {' '.join(authors)}")
                if not goodreads_book:
                    print(
                        f"!!! couldn't find any matches for {title} ({isbn}), aborting"
                    )
                    continue

                found_title, *_ = goodreads_book["title"].split(": ", 1)
                if found_title.lower() == title.lower():
                    print(f"found {title} on goodreads by name")
                    book = goodreads_create(data=goodreads_book)
                    book.isbn = isbn
                    book.edition_format = Book.Format.EBOOK
                    book.publisher = "Verso"
                    book.mark_owned()
                    book.save()
                else:
                    print(f"got {found_title} instead of {title}")
                    print(f"!!! need to manually import {title} ({isbn})")
