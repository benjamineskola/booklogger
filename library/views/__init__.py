from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_GET

from . import (  # noqa: F401
    author,
    book,
    importer,
    publisher,
    reading_list,
    report,
    search,
    series,
    stats,
    tags,
)


@require_GET
def robots_txt(request: HttpRequest) -> HttpResponse:
    lines = [
        "User-agent: *",
        "Disallow: /",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def add_slash(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    url = request.path + "/"
    if request.GET:
        url += "?" + request.GET.urlencode()

    return redirect(url, permanent=True)
