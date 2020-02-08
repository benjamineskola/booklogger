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

            if book.additional_authors.count() > 0:
                continue
            author = book.first_author
            if author.gender != 0:
                continue

            if "male-author" in shelves and not "female-author" in shelves:
                author.gender = 1
            elif "female-author" in shelves and not "male-author" in shelves:
                author.gender = 2
            else:
                print(f"don't know what to do with {book.title}")
            print(f"{author} -> {author.get_gender_display()}")
            author.save()
