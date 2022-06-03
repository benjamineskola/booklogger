from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse

from library.models import Book, Tag


def tag_cloud(request: HttpRequest) -> HttpResponse:
    tags = {
        "untagged": {
            "total": Book.objects.exclude(tags_list__contains=["non-fiction"])
            .exclude(tags_list__contains=["fiction"])
            .count()
        },
        "all": {tag.name: tag.books.count() for tag in Tag.objects.all()},
        "fiction": {tag.name: tag.books.fiction().count() for tag in Tag.objects.all()},
        "non-fiction": {
            tag.name: tag.books.nonfiction().count() for tag in Tag.objects.all()
        },
    }

    tags["fiction"]["no other tags"] = Tag.objects[
        "fiction"
    ].books_uniquely_tagged.count()
    tags["non-fiction"]["no other tags"] = Tag.objects[
        "non-fiction"
    ].books_uniquely_tagged.count()

    sorted_tags = {
        "name": {
            key: dict(sorted(tags[key].items(), key=lambda item: item[0]))
            for key in ["fiction", "non-fiction", "all"]
        },
        "size": {
            key: dict(sorted(tags[key].items(), key=lambda item: item[1], reverse=True))
            for key in ["fiction", "non-fiction", "all"]
        },
    }

    return TemplateResponse(
        request,
        "tag_list.html",
        {"page_title": "Tags", "tags": sorted_tags},
    )
