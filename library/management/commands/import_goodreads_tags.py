import csv
import sys

from django.core.management.base import BaseCommand

from library.models import Author, Book, BookAuthor


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("file", nargs="?")
        parser.add_argument("-f", "--force", action="store_true", default=False)

    def handle(self, **options):
        if options["force"]:
            Author.objects.all().delete()
            Book.objects.all().delete()
            BookAuthor.objects.all().delete()

        if options["file"]:
            csvfile = open(options["file"])
        else:
            csvfile = sys.stdin

        reader = csv.DictReader(csvfile)
        first_fail = 0
        second_fail = 0
        third_fail = 0
        for row in reader:
            data = dict(row)
            books = Book.objects.filter(goodreads_id=data["Book Id"])
            if len(books) != 1:
                title, *rest = data["Title"].split(":")
                title, *rest = title.split(" (")
                books = Book.objects.filter(title__icontains=title.strip())
                if len(books) != 1:
                    surname, *rest = data["Author l-f"].split(",")
                    books = Book.objects.filter(first_author__surname=surname)
                    if len(books) != 1:
                        print(f"skipping {data['Title']}")
                        continue
            book = books.first()
            shelves = data["Bookshelves"].split(", ")
            if not book.tags:
                book.tags = []
            for shelf in shelves:
                if shelf in [str(i) for i in range(2010, 2020)]:
                    continue
                if shelf in [
                    "abandoned",
                    "currently-reading",
                    "female-author",
                    "male-author",
                    "owned-books",
                    "owned-ebooks",
                    "public-domain",
                    "read",
                    "shared-books",
                    "to-read",
                    "wishlist",
                ]:
                    continue
                if not shelf in book.tags:
                    print(f"tagging {book.title} with {shelf}")
                    book.tags.append(shelf)
            if len(book.tags) < 2:
                book.tags.append("untagged")
            book.save()
