import json

import commonmark
from django.contrib.humanize.templatetags.humanize import ordinal
from django.templatetags.static import static
from django.urls import reverse
from library.utils import round_trunc

from jinja2 import Environment, Markup


def environment(**options):
    env = Environment(**options)
    env.globals.update({"static": static, "url": reverse})

    env.filters["markdown"] = lambda text: Markup(commonmark.commonmark(text))

    env.filters["json"] = json.dumps

    env.filters["ordinal"] = ordinal

    env.filters["round_trunc"] = round_trunc

    return env
