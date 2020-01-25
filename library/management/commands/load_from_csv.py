import csv

from django.core.management.base import BaseCommand

from library.models import Author, Book, BookAuthor


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("file")
        parser.add_argument("-f", "--force", action="store_true", default=False)

    def handle(self, **options):
        if options["force"]:
            Author.objects.all().delete()
            Book.objects.all().delete()
            BookAuthor.objects.all().delete()

        authors = {}
        books = []

        with open(options["file"], newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                book = dict(row)
                books.append(book)

                author_names = self._normalize(book["Author"])
                key = author_names[1] + ", " + author_names[0]

                if key not in authors:
                    author_data = {
                        "surname": author_names[0],
                        "forenames": author_names[1],
                        "books": [],
                        "pk": None,
                    }
                    authors[key] = author_data

                shelves = book["Bookshelves"].split(", ")
                book_format = 0
                if "owned-books" in shelves:
                    book_format = 1
                elif "owned-ebooks" in shelves:
                    book_format = 3
                elif "public_domain" in shelves:
                    book_format = 4

                title = book["Title"]
                series_name = ""
                series_order = 0

                if title[-1] == ")":
                    title, rest = title.split(" (", 2)
                    first_series = rest.split(";")[0]
                    series_name, *rest = first_series.split("#")
                    series_name = series_name.strip(" ,)")
                    if rest:
                        try:
                            series_order = float(rest[0].strip(")"))
                        except ValueError:
                            pass

                book_data = {
                    "title": title,
                    "series": series_name,
                    "series_order": series_order,
                    "owned": any(["owned-books" in shelves, "owned-ebooks" in shelves]),
                    "edition_format": book_format,
                    "goodreads_id": book["Book Id"],
                    "isbn": book["ISBN13"][2:-1],
                    "first_published": int(
                        book["Original Publication Year"]
                        if book["Original Publication Year"]
                        else 0
                    ),
                    "edition_published": int(
                        book["Year Published"] if book["Year Published"] else 0
                    ),
                    "publisher": book["Publisher"],
                    "page_count": int(
                        book["Number of Pages"] if book["Number of Pages"] else 0
                    ),
                }
                authors[key]["books"].append(book_data)

        for key, author in authors.items():
            a = Author(surname=author["surname"], forenames=author["forenames"])
            if options["force"]:
                a.save()

            for book in author["books"]:
                b = Book(**book)
                if options["force"]:
                    b.save()
                    ba = BookAuthor(book=b, author=a)
                    ba.save()

    def _normalize(self, raw_name):
        words = raw_name.split(" ")
        surname = words.pop()

        while words and words[-1].lower() in ["von", "van", "der", "le"]:
            surname = words.pop() + " " + surname

        forenames = " ".join(words)
        return (surname.strip(), forenames.strip())
