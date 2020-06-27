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

        authors = {}
        books = []

        if options["file"]:
            csvfile = open(options["file"])
        else:
            csvfile = sys.stdin

        reader = csv.DictReader(csvfile)
        for row in reader:
            book = dict(row)
            books.append(book)

            author_name = book["AUTHOR"]

            if author_name not in authors:
                author_data = {
                    "books": [],
                    "pk": None,
                }
                authors[author_name] = author_data

            book_format = 3

            title = book["TITLE"]

            if title[-1] == ")":
                title, *rest = title.split(" (", 2)

            book_data = {
                "title": title.strip(),
                "owned": False,
                "edition_format": book_format,
                "asin": book["ASIN"],
                "publisher": book["PUBLISHER"],
                "image_url": book["IMAGE URL"],
            }
            authors[author_name]["books"].append(book_data)

        for key, author in authors.items():
            a, created = Author.objects.get_or_create_by_single_name(author_name)
            if created:
                print(f"created {a}")
            else:
                print(f"using {a}")
                for book in author["books"]:
                    books = a.books.filter(title=book["title"])
                    if books.count():
                        print(f"  {books[0]} already exists")
                    else:
                        book["first_author"] = a
                        b = Book(**book)
                        b.save()
                        print(f"  creating {b}")
