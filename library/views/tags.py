from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from library.models import Book, Tag


def tag_cloud(request: HttpRequest) -> HttpResponse:
    tags = {
        "untagged": Book.objects.exclude(tags__contains=["non-fiction"])
        .exclude(tags__contains=["fiction"])
        .count(),
        "non-fiction": {
            "no other tags": Tag.objects["non-fiction"].books_uniquely_tagged.count()
        },
        "fiction": {
            "no other tags": Tag.objects["fiction"].books_uniquely_tagged.count()
        },
        "all": {},
    }

    for tag in Tag.objects.all():
        tags["all"][tag.name] = tag.books.count()
        tags["fiction"][tag.name] = tag.books.fiction().count()
        tags["non-fiction"][tag.name] = tag.books.nonfiction().count()

    sorted_tags = {"name": {}, "size": {}}
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
