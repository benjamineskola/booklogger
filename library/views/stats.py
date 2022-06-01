from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from library.models import Author, Book, BookQuerySet, LogEntry, LogEntryQuerySet
from library.utils import is_authenticated

GENRES = ["fiction", "non-fiction"]

Numeric = int | float


def _counts_for_queryset(
    books: BookQuerySet, total_count: int = 0, total_pages: int = 0
) -> dict[str, Numeric]:
    result: dict[str, Numeric] = {
        "count": books.count(),
        "pages": books.page_count,
    }

    if total_count:
        result["percent"] = (books.count() / total_count) * 100
    if total_pages:
        result["pages_percent"] = (books.page_count / total_pages) * 100

    return result


def _stats_for_queryset(books: BookQuerySet) -> dict[str, Any]:
    result: dict[str, Any] = _counts_for_queryset(books)
    result.update(
        {
            "average_pages": books.page_count
            / max(1, books.exclude(page_count=0).count()),
            "shortest_book": books.exclude(page_count=0).order_by("page_count").first(),
            "longest_book": books.exclude(page_count=0).order_by("page_count").last(),
            "breakdowns": {"gender": {}, "genre": {}},
        }
    )
    result.update(
        {
            genre: _counts_for_queryset(
                books.tagged(genre), result["count"], result["pages"]
            )
            for genre in GENRES
        }
    )
    result["both"] = _counts_for_queryset(
        books.by_multiple_genders(), result["count"], result["pages"]
    )
    result["poc"] = _counts_for_queryset(books.poc(), result["count"], result["pages"])

    gender_labels = {int(i): Author.Gender(i).label.lower() for i in Author.Gender}
    gender_labels[1] = "men"
    gender_labels[2] = "women"
    gender_labels[3] = "organisations"

    for i, label in gender_labels.items():
        result[label] = _counts_for_queryset(
            books.by_gender(i), result["count"], result["pages"]
        )

        result["breakdowns"]["gender"][label] = {
            genre: dict(
                key=i,
                **_counts_for_queryset(
                    books.tagged(genre).by_gender(i), result[label]["count"]
                )
            )
            for genre in GENRES
        }

    result["breakdowns"]["genre"] = {
        genre: {
            gender: dict(
                key=i,
                **_counts_for_queryset(
                    books.tagged(genre).by_gender(i), books.tagged(genre).count()
                )
            )
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
    year_days = (last_day - first_day).days + 1
    current_day = (timezone.datetime.now() - first_day).days + 1

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
