import datetime
import re
import sys

import yaml
from django.core.management.base import BaseCommand

from library.models import Author, Book, BookAuthor, LogEntry


def bear_list_to_yaml(data):
    yaml_data = "\n".join(data.split("\n"))
    yaml_data = re.sub(r"- ([0-9]+|In progress)\n", r"\1:\n", yaml_data)
    yaml_data = re.sub("\t", "    ", yaml_data)
    yaml_data = re.sub("[*-] (.*)", r'- "\1"', yaml_data)
    return yaml_data


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
        if options["force"]:
            LogEntry.objects.all().delete()

        self.processed_entries = []
        if options["file"]:
            input_data = open(options["file"]).read()
        else:
            input_data = sys.stdin.read()
        data = yaml.safe_load(bear_list_to_yaml(input_data))

        for year, books in data.items():
            for book in books:
                dates, rest = book.split(": ", 1)
                dates = dates.split("–")
                anthology = False
                try:
                    author, title = rest.split(", ", 1)

                    if author.endswith(" (ed.)"):
                        anthology = True
                        author = author[0:-6]

                    authors = author.split(" and ")

                except ValueError:
                    print(rest)

                title = re.sub(r"^_(.*)_\s*$", r"\1", title)
                if title.endswith(")"):
                    title = title.split(" (")[0]

                start_date_parts = dates[0].split("/")
                start_date_precision = 0
                if start_date_parts[1] == "??":
                    start_date_parts[1] = "1"
                    start_date_parts[2] = "1"
                    start_date_precision = 2
                elif start_date_parts[2] == "??":
                    start_date_parts[2] = "1"
                    start_date_precision = 1
                start_date = datetime.date(*[int(i) for i in start_date_parts])
                if len(dates) > 1 and dates[1]:
                    end_date_parts = dates[1].split("/")
                    end_date_precision = 0
                    if end_date_parts[1] == "??":
                        end_date_parts[1] = "1"
                        end_date_parts[2] = "1"
                        end_date_precision = 2
                    elif end_date_parts[2] == "??":
                        end_date_parts[2] = "1"
                        end_date_precision = 1
                    end_date = datetime.date(*[int(i) for i in end_date_parts])
                else:
                    end_date = None

                self.processed_entries.append(
                    {
                        "title": title,
                        "authors": authors,
                        "authors_split": self._normalize(authors[0]),
                        "start_date": start_date,
                        "end_date": end_date,
                        "start_date_precision": start_date_precision,
                        "end_date_precision": end_date_precision,
                        "anthology": anthology,
                    }
                )

        for entry in self.processed_entries:
            try:
                author = Author.objects.get(
                    surname=entry["authors_split"][0],
                    forenames=entry["authors_split"][1],
                )
            except:
                print(f"cannot find author {entry['authors']}")
                continue

            books = author.books.filter(title=entry["title"].strip())
            if not books or len(books) > 1:
                print(entry["title"] + " cannot be found")
                # authors = Author.objects.filter(
                #     surname=entry["authors_split"][0],
                #     forenames=entry["authors_split"][1],
                # )
                # if authors:
                print(
                    f"but {author} has books: {[book.title for book in author.books.all()]}"
                )
            else:
                book = books[0]
                log = LogEntry(
                    book=book,
                    start_date=entry["start_date"],
                    end_date=entry["end_date"],
                    start_precision=entry["start_date_precision"],
                    end_precision=entry["end_date_precision"],
                )
                book.want_to_read = False
                if options["force"]:
                    book.save()
                    log.save()
            # book = books[0]
            # print(book)
