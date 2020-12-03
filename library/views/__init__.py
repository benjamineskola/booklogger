from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from library.models import Author, Book, LogEntry, Tag

from . import author, book, importer, publisher, report, search, series  # noqa: F401


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def tag_cloud(request):
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


def _stats_for_queryset(books):
    fiction = books.fiction()
    nonfiction = books.nonfiction()
    poc = books.filter(
        Q(first_author__poc=True) | Q(additional_authors__poc=True)
    ).distinct()
    result = {
        "count": books.count(),
        "pages": books.page_count,
        "both": {
            "count": books.by_multiple_genders().count(),
            "pages": books.by_multiple_genders().page_count,
        },
        "fiction": {
            "count": fiction.count(),
            "pages": fiction.page_count,
        },
        "nonfiction": {
            "count": nonfiction.count(),
            "pages": nonfiction.page_count,
        },
        "poc": {
            "count": poc.count(),
            "pages": poc.page_count,
            "percent": poc.count() / books.count() * 100,
        },
        "breakdowns": {"gender": {}, "genre": {}},
    }

    gender_labels = {int(i): Author.Gender(i).label.lower() for i in Author.Gender}
    gender_labels[1] = "men"
    gender_labels[2] = "women"
    gender_labels[3] = "organisations"

    for i, label in gender_labels.items():
        result[label] = {
            "count": books.by_gender(i).count(),
            "pages": books.by_gender(i).page_count,
        }

        if result[label]:
            result[label]["percent"] = (
                result[label]["count"] / max(1, result["count"]) * 100
            )
        else:
            result[label]["percent"] = 0

        gender_fiction = fiction.by_gender(i)
        gender_nonfiction = nonfiction.by_gender(i)

        result["breakdowns"]["gender"][label] = {
            "key": i,
            "fiction": {
                "count": gender_fiction.count(),
                "percentage": gender_fiction.count()
                / max(1, result[label]["count"])
                * 100,
            },
            "nonfiction": {
                "count": gender_nonfiction.count(),
                "percentage": gender_nonfiction.count()
                / max(1, result[label]["count"])
                * 100,
            },
        }

    result["both"]["percent"] = result["both"]["count"] / max(1, result["count"]) * 100

    for category in list(gender_labels.values()) + [
        "both",
        "fiction",
        "nonfiction",
        "poc",
    ]:
        if result[category]["pages"]:
            result[category]["pages_percent"] = (
                result[category]["pages"] / max(1, result["pages"]) * 100
            )
        else:
            result[category]["pages_percent"] = 0

    for genre in ["fiction", "non-fiction"]:
        genre_books = books.tagged(genre)
        result["breakdowns"]["genre"][genre] = {}
        for i, gender in gender_labels.items():
            result["breakdowns"]["genre"][genre][gender] = {
                "key": i,
                "count": genre_books.by_gender(i).count(),
                "percentage": genre_books.by_gender(i).count()
                / max(1, genre_books.count())
                * 100,
            }

    return result


def stats_index(request):
    books = Book.objects.all()
    owned = books.filter(owned_by__username="ben")
    owned_count = owned.count()
    read_books = books.read()
    owned_read = owned.read().count()
    want_to_read = owned.filter(want_to_read=True)
    want_to_read_count = want_to_read.count()
    reread = owned.read().filter(want_to_read=True).count()

    years = (
        LogEntry.objects.exclude(end_date__isnull=True)
        .distinct("end_date__year")
        .values_list("end_date__year", flat=True)
    )

    return render(
        request,
        "stats_index.html",
        {
            "page_title": "Library Stats",
            "owned": owned_count,
            "owned_read": owned_read,
            "owned_read_pct": owned_read / owned_count * 100,
            "want_to_read": want_to_read_count,
            "want_to_read_pct": want_to_read_count / owned_count * 100,
            "reread": reread,
            "reread_pct": reread / read_books.count() * 100,
            "years": years,
        },
    )


def stats_for_year(request, year):
    books = Book.objects.all()
    read_books = books.read()

    if year == "total":
        result = _stats_for_queryset(read_books)
    else:
        if year == "sometime":
            year = 1
        result = _stats_for_queryset(books.filter(log_entries__end_date__year=year))
        result["acquired"] = books.filter(acquired_date__year=year).count()

    current_year = timezone.now().year
    prediction = {}
    if year == str(current_year):
        first_day = timezone.datetime(current_year, 1, 1)
        last_day = timezone.datetime(current_year, 12, 31)
        year_days = (last_day - first_day).days
        current_day = (timezone.datetime.now() - first_day).days
        current_week = (current_day // 7) + 1
        current_year_count = books.filter(
            log_entries__end_date__year=current_year
        ).count()
        prediction["predicted_count"] = current_year_count / current_day * year_days

        remaining_weeks = 52 - current_week
        prediction["target_counts"] = {}
        for target in [26, 39, 52, 78, 104, 208]:
            if target > current_year_count:
                prediction["target_counts"][target] = (
                    target - current_year_count
                ) / remaining_weeks
            if len(prediction["target_counts"].keys()) >= 3:
                break
    else:
        current_week = 52

    return render(
        request,
        "stats_for_year.html",
        {
            "page_title": "Library Stats",
            "year": str(year),
            "current_year": current_year,
            "current_week": current_week,
            "result": result,
            "prediction": prediction,
        },
    )


def add_slash(request, *args, **kwargs):
    url = request.path + "/"
    if request.GET:
        url += "?" + request.GET.urlencode()

    return redirect(url, permanent=True)
