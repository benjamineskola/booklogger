from django.core.management.base import BaseCommand, CommandParser

from library.models import Book
from library.utils import goodreads


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("-i", "--isbn", action="store_true", default=False)
        parser.add_argument("-a", "--asin", action="store_true", default=False)

    def handle(self, *_args: str, **options: str) -> None:
        if not options["isbn"] and not options["asin"]:
            print("no identifier chosen")
            return

        if options["isbn"]:
            self.handle_with("isbn")

        if options["asin"]:
            self.handle_with("asin")

    def handle_with(self, identifier: str) -> None:
        books = Book.objects.filter(owned_by__isnull=False)
        books = books.exclude(**{identifier: ""})

        if identifier == "isbn":
            books = books.filter(asin="")

        missing_count = 0
        mismatch_count = 0
        for book in books:
            query = getattr(book, identifier)

            gr_data = goodreads.find(query)
            if not gr_data:
                missing_count += 1
                print(f"\nCouldn't find goodreads data for {book}")
                continue

            gr_id = gr_data["goodreads_id"]
            if gr_id != book.goodreads_id:
                print(f"\nMISMATCH for {book}")
                mismatch_count += 1
                if (
                    input(
                        f"\nIs this the right edition? https://www.goodreads.com/book/show/{gr_id} [y/n]"
                    ).lower()
                    == "y"
                ):
                    book.goodreads_id = gr_id
                    book.save()
                else:
                    print("Ignoring it")
            else:
                print(".", end="", flush=True)

        print()
        print(f"{missing_count} missing")
        print(f"{mismatch_count} mismatches")
