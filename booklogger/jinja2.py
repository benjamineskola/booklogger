import commonmark
from django.templatetags.static import static
from django.urls import reverse

from jinja2 import Environment, Markup
from library.utils import get_hyperlink, oxford_comma


def environment(**options):
    env = Environment(**options)
    env.globals.update({"static": static, "url": reverse})
    env.filters.update({"oxford_comma": oxford_comma, "get_hyperlink": get_hyperlink})

    env.filters["markdown"] = lambda text: Markup(commonmark.commonmark(text))
    return env
