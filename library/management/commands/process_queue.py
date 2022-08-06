from time import sleep

from django.core.management.base import BaseCommand

from library.models import Queue
from library.utils import create


class Command(BaseCommand):
    def handle(self, *_args: str, **_options: str) -> None:
        while True:
            errors = 0
            while Queue.objects.count():
                if errors == Queue.objects.count():
                    break
                print(f"===== {Queue.objects.count()} =====")
                data = {}
                try:
                    item = Queue.objects.first()
                    if not item:
                        break
                    data = item.data
                    item.delete()

                    book, created, authors = create.book(
                        item.data, owned=item.data.get("owned", False)
                    )
                    if created:
                        print(f"created {book}")
                    else:
                        print(f"updated {book}")
                    for author, created in authors:
                        if created:
                            print(f"created {author}")
                        else:
                            print(f"updated {author}")
                except Exception as e:  # pylint: disable=broad-except
                    errors += 1
                    print(f"===== error: {e} =====")
                    item = Queue(data=data)
                    item.save()
            sleep(60)
