import commonmark
from django.templatetags.static import static
from django.urls import reverse

from jinja2 import Environment, Markup
from library.utils import get_hyperlink, oxford_comma


def environment(**options):
    env = Environment(**options)
    env.globals.update({"static": static, "url": reverse})

    env.filters["get_hyperlink"] = lambda *args, **kwargs: Markup(
        get_hyperlink(*args, **kwargs)
    )
    env.filters["markdown"] = lambda text: Markup(commonmark.commonmark(text))
    env.filters["oxford_comma"] = lambda l: Markup(oxford_comma(l))

    return env
