import json

import commonmark
from django.contrib.humanize.templatetags.humanize import ordinal
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment, Markup

from library.utils import oxford_comma, round_trunc


def environment(**options):
    env = Environment(**options, trim_blocks=True, lstrip_blocks=True)
    env.globals.update({"static": static, "url": reverse})

    env.filters["markdown"] = lambda text: Markup(commonmark.commonmark(text))

    env.filters["json"] = json.dumps

    env.filters["ordinal"] = ordinal

    env.filters["round_trunc"] = round_trunc

    env.filters["oxford_comma"] = oxford_comma

    return env
