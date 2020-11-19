from django.db.models import Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from library.models import Book, LogEntry, Tag

from . import author, book, importer, report, search, series  # noqa: F401

# Create your views here.


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
        "pages": books.aggregate(Sum("page_count"))["page_count__sum"],
        "men": books.by_men().count(),
        "men_pages": books.by_men().aggregate(Sum("page_count"))["page_count__sum"],
        "women": books.by_women().count(),
        "women_pages": books.by_women().aggregate(Sum("page_count"))["page_count__sum"],
        "both": books.by_multiple_genders().count(),
        "both_pages": books.by_multiple_genders().aggregate(Sum("page_count"))[
            "page_count__sum"
        ],
        "nonbinary": books.by_gender(4).count(),
        "nonbinary_pages": books.by_gender(4).aggregate(Sum("page_count"))[
            "page_count__sum"
        ],
        "organisations": books.filter(first_author__gender=3).count(),
        "organisations_pages": books.exclude(first_author__gender=3).aggregate(
            Sum("page_count")
        )["page_count__sum"],
        "fiction": fiction.count(),
        "fiction_pages": fiction.aggregate(Sum("page_count"))["page_count__sum"],
        "nonfiction": nonfiction.count(),
        "nonfiction_pages": nonfiction.aggregate(Sum("page_count"))["page_count__sum"],
        "poc": poc.count(),
        "poc_pages": poc.aggregate(Sum("page_count"))["page_count__sum"],
        "poc_percentage": poc.count() / books.count() * 100,
        "breakdowns": {},
    }

    for category in ["men", "women", "nonbinary", "both", "organisations"]:
        result[category + "_percent"] = result[category] / max(1, result['count']) * 100

    for category in ["men", "women", "fiction", "nonfiction", "poc"]:
        if result[category + "_pages"]:
            result[category + "_pages_percent"] = (
                result[category + "_pages"] / max(1, result["pages"]) * 100
            )
        else:
            result[category + "_pages_percent"] = 0

    for gender, i in [("men", 1), ("women", 2)]:
        gender_fiction = fiction.by_gender(i)
        gender_nonfiction = nonfiction.by_gender(i)

        result["breakdowns"][gender] = {
            "fiction_count": gender_fiction.count(),
            "percentage_fiction": gender_fiction.count() / max(1, result[gender]) * 100,
            "nonfiction_count": gender_nonfiction.count(),
            "percentage_nonfiction": gender_nonfiction.count()
            / max(1, result[gender])
            * 100,
        }
    for genre in ["fiction", "non-fiction"]:
        genre_books = Tag.objects[genre].books
        result["breakdowns"][genre] = {
            "men_count": genre_books.by_men().count(),
            "women_count": genre_books.by_women().count(),
            "percentage_men": genre_books.by_men().count()
            / max(1, genre_books.count())
            * 100,
            "percentage_women": genre_books.by_women().count()
            / max(1, genre_books.count())
            * 100,
        }
    return result


def stats(request):
    books = Book.objects.all()
    owned = books.filter(owned_by__username="ben")
    owned_count = owned.count()
    read_books = books.read()
    owned_read = owned.read().count()
    want_to_read = owned.filter(want_to_read=True)
    want_to_read_count = want_to_read.count()
    reread = owned.read().filter(want_to_read=True).count()

    books_by_year = {}  # {"all": {"books": books, "count": books.count()}}

    for year in (
        LogEntry.objects.exclude(end_date__isnull=True)
        .distinct("end_date__year")
        .values_list("end_date__year", flat=True)
    ):
        books_by_year[str(year)] = _stats_for_queryset(
            books.filter(log_entries__end_date__year=year)
        )

        books_by_year[str(year)]["acquired"] = books.filter(
            acquired_date__year=year
        ).count()

    books_by_year["total"] = _stats_for_queryset(read_books)

    current_year = timezone.now().year
    first_day = timezone.datetime(current_year, 1, 1)
    last_day = timezone.datetime(current_year, 12, 31)
    year_days = (last_day - first_day).days
    current_day = (timezone.datetime.now() - first_day).days
    current_week = (current_day // 7) + 1
    current_year_count = books.filter(log_entries__end_date__year=current_year).count()
    predicted_count = current_year_count / current_day * year_days

    remaining_weeks = 52 - current_week
    target_counts = {}
    for target in [26, 39, 52, 78, 104, 208]:
        if target > current_year_count:
            target_counts[target] = (target - current_year_count) / remaining_weeks
        if len(target_counts.keys()) >= 3:
            break

    return render(
        request,
        "stats.html",
        {
            "page_title": "Library Stats",
            "owned": owned_count,
            "owned_read": owned_read,
            "owned_read_pct": owned_read / owned_count * 100,
            "want_to_read": want_to_read_count,
            "want_to_read_pct": want_to_read_count / owned_count * 100,
            "reread": reread,
            "reread_pct": reread / read_books.count() * 100,
            "current_year": current_year,
            "current_week": current_week,
            "predicted_count": predicted_count,
            "books_by_year": books_by_year,
            "target_counts": target_counts,
        },
    )


def add_slash(request, *args, **kwargs):
    url = request.path + "/"
    if request.GET:
        url += "?" + request.GET.urlencode()

    return redirect(url, permanent=True)
