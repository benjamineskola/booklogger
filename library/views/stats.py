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

    current_year = timezone.now().year
    current_day, year_days = calculate_year_progress(current_year)
    current_week = (current_day // 7) + 1

    all_time_average_pages = read_books.page_count / max(
        1, read_books.exclude(page_count=0).count()
    )
    gender_labels = {
        "1": "men",
        "2": "women",
        "3": "organisations",
        "4": "non-binary people",
    }

    years = [
        0,
        *list(
            StatisticsReport.objects.exclude(year=0)
            .order_by("year")
            .reverse()
            .values_list("year", flat=True)
        ),
    ]
    reports = [_get_stats_object(year, current_year) for year in years]

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
            "reports": reports,
            "all_time_average_pages": all_time_average_pages,
            "current_year": current_year,
            "current_week": current_week,
            "gender_labels": gender_labels,
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


def _get_stats_object(year: int, current_year: int) -> dict[str, Any]:
    result: dict[str, Any] = list(StatisticsReport.objects.filter(year=year).values())[  # type: ignore[assignment]
        0
    ]
    current_year = timezone.now().year

    log_entries = LogEntry.objects.filter(exclude_from_stats=False, abandoned=False)

    if year > 0:
        result["acquired"] = Book.objects.filter(acquired_date__year=year).count()
        log_entries = log_entries.filter(end_date__year=year)

    result["longest"] = Book.objects.get(id=result["longest_id"])
    result["shortest"] = Book.objects.get(id=result["shortest_id"])

    if year == current_year:
        result["prediction"], result["target_counts"] = make_prediction(
            current_year, log_entries
        )

        current_day, year_days = calculate_year_progress(current_year)
        result["pages_per_day"] = result["page_count"] / current_day
        result["predicted_pages"] = result["pages_per_day"] * year_days
    elif year > 1:
        result["pages_per_day"] = result["page_count"] / (
            366 if int(year) % 4 == 0 else 365
        )  # technically incorrect but valid until AD 2100.

    return result
