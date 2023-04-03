import logging
from time import sleep

from django.core.management.base import BaseCommand

from library.models import Queue
from library.utils import create

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *_args: str, **_options: str) -> None:
        while True:
            errors = 0
            while Queue.objects.count():
                if errors == Queue.objects.count():
                    break
                data = {}
                try:
                    item = Queue.objects.first()
                    if not item:
                        break
                    data = item.data
                    item.delete()

                    owned = item.data.get("owned", False)
                    if "owned" in item.data:
                        del item.data["owned"]
                    book, created, authors = create.book(item.data, owned=owned)
                    if created:
                        logger.info("created %s", book)
                    else:
                        logger.info("updated %s", book)
                    for author, created in authors:
                        if created:
                            logger.info("created %s", author)
                        else:
                            logger.info("updated %s", author)
                except Exception as e:  # noqa: BLE001
                    errors += 1
                    logger.warning("===== error: %s =====", e)
                    item = Queue(data=data)
                    item.save()
            sleep(60)
