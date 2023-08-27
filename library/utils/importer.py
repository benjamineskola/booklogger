import logging
import threading
from collections.abc import Sequence
from typing import Any

from library.utils import create

logger = logging.getLogger(__name__)


def _process_record(record: dict[str, Any]) -> None:
    owned = record.get("owned", False)
    if "owned" in record:
        del record["owned"]
    book, created, authors = create.book(record, owned=owned)
    if created:
        logger.info("created %s", book)
    else:
        logger.info("updated %s", book)
    for author, created in authors:
        if created:
            logger.info("created %s", author)
        else:
            logger.info("updated %s", author)


def _process_in_thread(records: Sequence[dict[str, Any]]) -> None:
    for record in records:
        _process_record(record)


def process(records: Sequence[dict[str, Any]]) -> None:
    thread = threading.Thread(target=_process_in_thread, args=[records])
    thread.start()
