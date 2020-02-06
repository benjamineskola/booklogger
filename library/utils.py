from library.models import Author


def oxford_comma(items):
    if len(items) > 2:
        items[-1] = "and " + items[-1]
        return ", ".join(items)
    else:
        return " and ".join(items)


def get_hyperlink(item, book=None):
    return '<a href="{url}">{text}</a>'.format(**(item.get_link_data(book=book)))
