import json
import urllib.parse
from typing import Any

import commonmark
from crispy_forms.templatetags.crispy_forms_filters import as_crispy_field
from django.contrib.humanize.templatetags.humanize import intcomma, ordinal
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment, Markup  # type: ignore [attr-defined]

from library.utils import oxford_comma, round_trunc


def environment(**options: Any) -> Environment:
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
            "quote": urllib.parse.quote,
        }
    )

    return env
