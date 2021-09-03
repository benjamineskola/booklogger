from typing import Dict

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from library.models import Book, BookQuerySet, Tag


def tag_cloud(request: HttpRequest) -> HttpResponse:
    tags: Dict[str, Dict[str, int]] = {
        "untagged": {
            "total": Book.objects.exclude(tags__contains=["non-fiction"])
            .exclude(tags__contains=["fiction"])
            .count()
        },
        "non-fiction": {
            "no other tags": Tag.objects["non-fiction"].books_uniquely_tagged.count()
        },
        "fiction": {
            "no other tags": Tag.objects["fiction"].books_uniquely_tagged.count()
        },
        "all": {},
    }

    for tag in Tag.objects.all():
        books: BookQuerySet = tag.books  # type: ignore [assignment]
        tags["all"][tag.name] = books.count()
        tags["fiction"][tag.name] = books.fiction().count()
        tags["non-fiction"][tag.name] = books.nonfiction().count()

    sorted_tags: Dict[str, Dict[str, Dict[str, int]]] = {"name": {}, "size": {}}
    for key in ["fiction", "non-fiction", "all"]:
        sorted_tags["name"][key] = {
            k: v for k, v in sorted(tags[key].items(), key=lambda item: item[0])
        }
    for key in ["fiction", "non-fiction", "all"]:
        sorted_tags["size"][key] = {
            k: v
            for k, v in sorted(
                tags[key].items(), key=lambda item: item[1], reverse=True
            )
        }

    return render(
        request,
        "tag_list.html",
        {"page_title": "Tags", "tags": sorted_tags},
    )
