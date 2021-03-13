import json
import urllib.parse

import commonmark
import unidecode
from crispy_forms.templatetags.crispy_forms_filters import as_crispy_field
from django.contrib.humanize.templatetags.humanize import intcomma, ordinal
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment, Markup

from library.utils import oxford_comma, round_trunc


def environment(**options):
    env = Environment(**options, trim_blocks=True, lstrip_blocks=True)

    env.globals.update(
        {
            "set": set,
            "static": static,
            "url": reverse,
        }
    )

    env.filters.update(
        {
            "intcomma": intcomma,
            "json": json.dumps,
            "markdown": lambda text: Markup(commonmark.commonmark(text)),
            "ordinal": ordinal,
            "oxford_comma": oxford_comma,
            "round_trunc": round_trunc,
            "crispy": as_crispy_field,
            "unidecode": lambda text: unidecode.unidecode(text),
            "quote": lambda text: urllib.parse.quote(text),
        }
    )

    return env
