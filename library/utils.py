from typing import Any, List

from django.conf import settings

LANGUAGES = sorted(
    set(
        [
            (l, y.split(" ", 1)[-1])
            for x, y in settings.LANGUAGES
            if len(l := x.split("-", 1)[0]) == 2
        ]
    )
)


def oxford_comma(items: List[str]) -> str:
    if len(items) > 2:
        items[-1] = "and " + items[-1]
        return ", ".join(items)
    else:
        return " and ".join(items)


def get_hyperlink(item: Any, book: Any = None) -> str:
    return '<a href="{url}">{text}</a>'.format(**(item.get_link_data(book=book)))
