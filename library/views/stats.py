from typing import Any

from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from library.models import Author, Book, BookQuerySet, LogEntry, LogEntryQuerySet
from library.utils import is_authenticated

GENRES = ["fiction", "non-fiction"]


def _stats_for_queryset(books: BookQuerySet) -> dict[str, Any]:
    poc = books.filter(
        Q(first_author__poc=True) | Q(additional_authors__poc=True)
    ).distinct()
    result: dict[str, Any] = {
        "count": books.count(),
        "pages": books.page_count,
        "average_pages": books.page_count / max(1, books.exclude(page_count=0).count()),
        "shortest_book": books.exclude(page_count=0).order_by("page_count").first(),
        "longest_book": books.exclude(page_count=0).order_by("page_count").last(),
        "both": {
            "count": books.by_multiple_genders().count(),
            "pages": books.by_multiple_genders().page_count,
        },
        "poc": {
            "count": poc.count(),
            "pages": poc.page_count,
            "percent": poc.count() / max(1, books.count()) * 100,
        },
        "breakdowns": {"gender": {}, "genre": {}},
    }
    result.update(
        {
            genre: {
                "count": books.tagged(genre).count(),
                "pages": books.tagged(genre).page_count,
            }
            for genre in GENRES
        }
    )

    gender_labels = {int(i): Author.Gender(i).label.lower() for i in Author.Gender}
    gender_labels[1] = "men"
    gender_labels[2] = "women"
    gender_labels[3] = "organisations"

    for i, label in gender_labels.items():
        result[label] = {
            "count": books.by_gender(i).count(),
            "pages": books.by_gender(i).page_count,
        }

        result[label]["percent"] = (
            result[label].get("count", 0) / max(1, result["count"]) * 100
        )

        result["breakdowns"]["gender"][label] = {
            genre: {
                "count": books.tagged(genre).by_gender(i).count(),
                "percentage": books.tagged(genre).by_gender(i).count()
                / max(1, result[label]["count"])
                * 100,
            }
            for genre in GENRES
        }
        result["breakdowns"]["gender"][label]["key"] = i

    result["both"]["percent"] = result["both"]["count"] / max(1, result["count"]) * 100

    for category in list(gender_labels.values()) + [
        "both",
        "fiction",
        "non-fiction",
        "poc",
    ]:
        result[category]["pages_percent"] = (
            result[category].get("pages", 0) / max(1, result["pages"]) * 100
        )

    result["breakdowns"]["genre"] = {
        genre: {
            gender: {
                "key": i,
                "count": books.tagged(genre).by_gender(i).count(),
                "percentage": books.tagged(genre).by_gender(i).count()
                / max(1, books.tagged(genre).count())
                * 100,
            }
            for i, gender in gender_labels.items()
        }
        for genre in GENRES
    }

    return result


def stats_index(request: HttpRequest) -> HttpResponse:
    books = Book.objects.all()
    if not is_authenticated(request):
        books = books.filter(private=False)

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
        .exclude(abandoned=True)
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


def calculate_year_progress(year: int) -> tuple[int, int]:
    first_day = timezone.datetime(year, 1, 1)
    last_day = timezone.datetime(year, 12, 31)
    year_days = (last_day - first_day).days
    current_day = (timezone.datetime.now() - first_day).days

    return current_day, year_days


def make_prediction(
    year: int, log_entries: LogEntryQuerySet
) -> tuple[dict[str, float], dict[int, float]]:
    prediction = {}
    target_counts = {}

    current_day, year_days = calculate_year_progress(year)
    current_year_count = log_entries.count()
    prediction["predicted_count"] = current_year_count / max(1, current_day) * year_days

    remaining_days = year_days - current_day
    for target in [26, 39, 52, 78, 104, 208]:
        if target > current_year_count:
            target_counts[target] = (
                (target - current_year_count) / max(1, remaining_days) * 7
            )
        if len(target_counts.keys()) >= 3:
            break

    return prediction, target_counts


def stats_for_year(request: HttpRequest, year: str) -> HttpResponse:
    result: dict[str, Any] = {
        "page_title": "Library Stats",
        "year": "1" if year == "sometime" else year,
        "current_week": 52,  # potentially overridden later
        "current_year": timezone.now().year,
        "result": {},
    }

    log_entries = LogEntry.objects.filter(exclude_from_stats=False, abandoned=False)
    if year != "total":
        log_entries = log_entries.filter(end_date__year=result["year"])
        result["result"]["acquired"] = Book.objects.filter(
            acquired_date__year=year
        ).count()

    read_books = Book.objects.filter(id__in=log_entries.values_list("book", flat=True))

    if not is_authenticated(request):
        read_books = read_books.filter(private=False)

    result["result"].update(_stats_for_queryset(read_books))

    if year == str(result["current_year"]):
        result["prediction"], result["target_counts"] = make_prediction(
            result["current_year"], log_entries
        )

        current_day, year_days = calculate_year_progress(result["current_year"])
        result["current_week"] = (current_day // 7) + 1
        result["result"]["pages_per_day"] = result["result"]["pages"] / current_day
        result["result"]["predicted_pages"] = (
            result["result"]["pages_per_day"] * year_days
        )

    elif year not in ("total", "sometime"):
        result["result"]["pages_per_day"] = result["result"]["pages"] / (
            366 if int(year) % 4 == 0 else 365
        )  # technically incorrect but valid until AD 2100.

    result["all_time_average_pages"] = Book.objects.read().page_count / max(
        1, Book.objects.read().exclude(page_count=0).count()
    )

    return render(
        request,
        "stats_for_year.html",
        result,
    )
