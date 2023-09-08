from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET

from . import (  # noqa: F401
    author,
    book,
    importer,
    log_entry,
    publisher,
    reading_list,
    report,
    search,
    series,
    stats,
    tags,
)


@require_GET
def robots_txt(_request: HttpRequest) -> HttpResponse:
    lines = [
        "User-agent: *",
        "Disallow: /",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
