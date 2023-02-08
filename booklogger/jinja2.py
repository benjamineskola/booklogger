import json
import urllib.parse
from collections.abc import Iterable
from datetime import date, datetime
from itertools import groupby
from typing import Any, TypeVar

import commonmark
from crispy_forms.templatetags.crispy_forms_filters import as_crispy_field
from django.contrib.humanize.templatetags.humanize import intcomma, ordinal
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment
from markupsafe import Markup

from library.utils import oxford_comma, round_trunc

V = TypeVar("V")


def groupby_date(
    value: Iterable[V],
    attribute: str,
    *_: Any,
    fmt: str = "%d %B, %Y",
    default: str = "None",
    rev: bool = False,
) -> list[tuple[str, list[V]]]:
    def attrgetter_sort(item: Any) -> Any:
        result = getattr(item, attribute)
        undefined = (result is not None) if rev else (result is None)
        return (undefined, result)

    def attrgetter_fmt(item: Any) -> str:
        if result := getattr(item, attribute):
            if isinstance(result, date | datetime):
                if result.year == 1:
                    return default

                return result.strftime(fmt)
            return str(result)
        return default

    return [
        (key, list(values))
        for key, values in groupby(sorted(value, key=attrgetter_sort), attrgetter_fmt)
    ]


def environment(**options: Any) -> Environment:
    env = Environment(**options, trim_blocks=True, lstrip_blocks=True)  # noqa: S701

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
            "groupby_date": groupby_date,
        }
    )

    return env
