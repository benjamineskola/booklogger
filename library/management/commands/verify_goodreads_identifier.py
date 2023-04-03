import logging

from django.core.management.base import BaseCommand, CommandParser

from library.models import Book
from library.utils import goodreads

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("-i", "--isbn", action="store_true", default=False)
        parser.add_argument("-a", "--asin", action="store_true", default=False)

    def handle(self, *_args: str, **options: str) -> None:
        if not options["isbn"] and not options["asin"]:
            logger.warning("no identifier chosen")
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
                logger.warning("\nCouldn't find goodreads data for %s", book)
                continue

            gr_id = gr_data["goodreads_id"]
            if gr_id != book.goodreads_id:
                logger.warning("\nMISMATCH for %s", book)
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
                    logger.warning("Ignoring it")

        logger.warning("")
        logger.warning("%s missing", missing_count)
        logger.warning("%s mismatches", mismatch_count)
