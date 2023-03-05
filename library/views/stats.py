from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from library.models import Book, LogEntry, LogEntryQuerySet, StatisticsReport
from library.utils import is_authenticated


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

    years = StatisticsReport.objects.exclude(year=0).values_list("year", flat=True)

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
    first_day = timezone.datetime(year, 1, 1)  # type: ignore[attr-defined]
    last_day = timezone.datetime(year, 12, 31)  # type: ignore[attr-defined]
    year_days = (last_day - first_day).days + 1
    current_day = (timezone.datetime.now() - first_day).days + 1  # type: ignore[attr-defined]

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
        "year": 1 if year == "sometime" else 0 if year == "total" else int(year),
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

    result["report"], _ = StatisticsReport.objects.get_or_create(year=result["year"])

    if year == str(result["current_year"]):
        result["prediction"], result["target_counts"] = make_prediction(
            result["current_year"], log_entries
        )

        current_day, year_days = calculate_year_progress(result["current_year"])
        result["current_week"] = (current_day // 7) + 1
        result["pages_per_day"] = result["report"].page_count / current_day
        result["predicted_pages"] = result["pages_per_day"] * year_days

    elif year not in ("total", "sometime"):
        result["pages_per_day"] = result["report"].page_count / (
            366 if int(year) % 4 == 0 else 365
        )  # technically incorrect but valid until AD 2100.

    result["all_time_average_pages"] = Book.objects.read().page_count / max(
        1, Book.objects.read().exclude(page_count=0).count()
    )

    result["gender_labels"] = {
        "1": "men",
        "2": "women",
        "3": "organisations",
        "4": "non-binary people",
    }

    return render(
        request,
        "stats_for_year.html",
        result,
    )
