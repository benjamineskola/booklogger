from typing import Any, List


def oxford_comma(items: List[str]) -> str:
    if len(items) > 2:
        items[-1] = "and " + items[-1]
        return ", ".join(items)
    else:
        return " and ".join(items)


def get_hyperlink(item: Any, book: Any = None) -> str:
    return '<a href="{url}">{text}</a>'.format(**(item.get_link_data(book=book)))
