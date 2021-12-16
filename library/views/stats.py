from typing import Any

from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from library.models import Author, Book, BookQuerySet, LogEntry


def _stats_for_queryset(books: BookQuerySet) -> dict[str, Any]:
    fiction = books.fiction()
    nonfiction = books.nonfiction()
    poc = books.filter(
        Q(first_author__poc=True) | Q(additional_authors__poc=True)
    ).distinct()
    result: dict[str, Any] = {
        "count": books.count(),
        "pages": books.page_count,
        "average_pages": books.page_count
        / max(1, books.exclude(page_count__isnull=True).count()),
        "shortest_book": books.order_by("page_count").first(),
        "longest_book": books.exclude(page_count__isnull=True)
        .order_by("page_count")
        .last(),
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
            "percent": poc.count() / max(1, books.count()) * 100,
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


def stats_index(request: HttpRequest) -> HttpResponse:
    books = Book.objects.all()
    owned = books.owned()
    owned_count = owned.count()
    read_books = books.read()
    owned_read = owned.read().count()
    want_to_read = owned.filter(want_to_read=True)
    want_to_read_count = want_to_read.count()
    reread = owned.read().filter(want_to_read=True).count()
    unowned_read = books.unowned().read().count()

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
            "unowned_read": unowned_read,
            "want_to_read": want_to_read_count,
            "want_to_read_pct": want_to_read_count / owned_count * 100,
            "reread": reread,
            "reread_pct": reread / read_books.count() * 100,
            "years": years,
        },
    )


def stats_for_year(request: HttpRequest, year: str) -> HttpResponse:
    books = Book.objects.all()

    if year == "total":
        read_books = Book.objects.filter(
            id__in=LogEntry.objects.exclude(exclude_from_stats=True).values_list(
                "book", flat=True
            )
        )
        result = _stats_for_queryset(read_books)
    else:
        if year == "sometime":
            year = "1"
        read_books = Book.objects.filter(
            id__in=LogEntry.objects.exclude(exclude_from_stats=True)
            .filter(end_date__year=year)
            .values_list("book", flat=True)
        )
        result = _stats_for_queryset(read_books)
        result["acquired"] = books.filter(acquired_date__year=year).count()

    current_year = timezone.now().year
    prediction = {}
    target_counts = {}
    if year == str(current_year):
        first_day = timezone.datetime(current_year, 1, 1)
        last_day = timezone.datetime(current_year, 12, 31)
        year_days = (last_day - first_day).days
        current_day = (timezone.datetime.now() - first_day).days
        current_week = (current_day // 7) + 1
        current_year_count = books.filter(
            log_entries__end_date__year=current_year
        ).count()
        prediction["predicted_count"] = (
            current_year_count / max(1, current_day) * year_days
        )

        result["pages_per_day"] = result["pages"] / current_day
        result["predicted_pages"] = result["pages_per_day"] * year_days

        remaining_days = year_days - current_day
        for target in [26, 39, 52, 78, 104, 208]:
            if target > current_year_count:
                target_counts[target] = (
                    (target - current_year_count) / max(1, remaining_days) * 7
                )
            if len(target_counts.keys()) >= 3:
                break
    else:
        if year not in ("total", "sometime"):
            result["pages_per_day"] = result["pages"] / (
                366 if int(year) % 4 == 0 else 365
            )
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
            "target_counts": target_counts,
            "all_time_average_pages": books.read().page_count
            / max(1, books.read().exclude(page_count__isnull=True).count()),
        },
    )
