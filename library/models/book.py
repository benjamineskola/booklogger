import logging
import operator
import re
from collections.abc import Sequence  # noqa: F401
from datetime import date
from functools import reduce
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from django.contrib.auth.models import User
from django.db import models
from django.db.models import CheckConstraint, F, Q, Sum, Value
from django.db.models.functions import Concat, Lower
from django.db.models.indexes import Index
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from library.models.abc import SluggableModel, TimestampedModel
from library.models.book_with_editions import BookWithEditions
from library.utils import (
    LANGUAGES,
    clean_publisher,
    flatten,
    goodreads,
    google,
    isbn_to_isbn10,
    oxford_comma,
    remove_stopwords,
    smarten,
    str2bool,
    verso,
)

from .author import Author

if TYPE_CHECKING:
    from .log_entry import LogEntry  # pragma: no cover

logger = logging.getLogger(__name__)


class BaseBookManager(models.Manager["Book"]):
    def search(self, pattern: str) -> "BookQuerySet":
        words = pattern.lower().split()
        sql_pattern = "%" + "%".join(words) + "%"
        query = (
            Q(full_title__like=sql_pattern)
            | Q(edition_full_title__like=sql_pattern)
            | Q(
                author_name__like=sql_pattern,
            )
        )
        for word in words:
            query |= Q(tags__name__in=[word])

        # in order to query both title and subtitle together
        books = Book.objects.annotate(
            full_title=Lower(Concat("title", Value(": "), "subtitle")),
            edition_full_title=Lower(
                Concat("edition_title", Value(": "), "edition_subtitle")
            ),
            author_name=Lower(F("first_author__surname")),
        )
        return books.filter(query)


class BookQuerySet(models.QuerySet["Book"]):
    def by_gender(self, *genders: int) -> "BookQuerySet":
        return self.filter(
            Q(first_author__gender__in=genders)
            | Q(additional_authors__gender__in=genders)
        ).distinct()

    def by_men(self) -> "BookQuerySet":
        return self.by_gender(1)

    def by_women(self) -> "BookQuerySet":
        return self.by_gender(2)

    def by_multiple_genders(self) -> "BookQuerySet":
        return (
            self.exclude(additional_authors__isnull=True)
            .filter(additional_authors__gender__ne=F("first_author__gender"))
            .distinct()
        )

    def tagged(self, *tag_names: str) -> "BookQuerySet":
        qs = self.distinct()
        for tag_name in tag_names:
            qs &= Tag.objects.get(name=tag_name).books_recursive.distinct()
        return qs

    def fiction(self) -> "BookQuerySet":
        return self.tagged("fiction")

    def nonfiction(self) -> "BookQuerySet":
        return self.tagged("non-fiction")

    def read(self) -> "BookQuerySet":
        return self.filter(
            Q(log_entries__end_date__isnull=False, log_entries__abandoned=False)
            | Q(
                parent_edition__log_entries__end_date__isnull=False,
                parent_edition__log_entries__abandoned=False,
            )
        ).distinct()

    def unread(self) -> "BookQuerySet":
        return self.exclude(
            Q(log_entries__end_date__isnull=False)
            | Q(parent_edition__log_entries__end_date__isnull=False)
        ).distinct()

    def owned(self) -> "BookQuerySet":
        return self.owned_by("ben")

    def owned_by(self, user: str) -> "BookQuerySet":
        return self.filter(
            Q(owned_by__username=user)
            | Q(parent_edition__owned_by__username=user)
            # I can't make this recurse but three levels is the most I can foresee needing
            | Q(parent_edition__parent_edition__owned_by__username=user)
        )

    def owned_by_any(self) -> "BookQuerySet":
        return self.filter(owned_by__isnull=False)

    def available(self) -> "BookQuerySet":
        return self.owned_by("ben") | self.owned_by("sara") | self.borrowed()

    def borrowed(self) -> "BookQuerySet":
        return self.exclude(owned_by=None).unowned() | self.filter(was_borrowed=True)

    def unowned(self) -> "BookQuerySet":
        return self.filter(
            owned_by__isnull=True,
            parent_edition__owned_by__isnull=True,
            parent_edition__parent_edition__owned_by__isnull=True,
        )

    def poc(self, is_poc: bool = True) -> "BookQuerySet":  # noqa: FBT001, FBT002
        return self.filter(
            Q(first_author__poc=is_poc, first_author_role__in=["", "author", "editor"])
            | Q(
                id__in=BookAuthor.objects.filter(
                    role__in=["", "author", "editor"], author__poc=is_poc
                ).values_list("book", flat=True)
            )
        )

    def filter_by_request(self, request: Any) -> "BookQuerySet":
        qs = self
        match request.GET.get("gender", "").lower():
            case "multiple":
                qs = qs.by_multiple_genders()
            case "nonmale":
                qs = qs.by_gender(0, 2, 4)
            case gender if gender:
                if not gender.isdigit():
                    gender = Author.Gender[gender.upper()]
                qs = qs.by_gender(gender)

        if poc := request.GET.get("poc"):
            qs = qs.poc(str2bool(poc))
        if tags := request.GET.get("tags"):
            qs = qs.tagged(*[tag.strip() for tag in tags.lower().split(",")])
        if owned := request.GET.get("owned"):
            match owned.lower():
                case "borrowed":
                    qs = qs.borrowed()
                case "available":
                    qs = qs.available()
                case "yes" | "no" | "true" | "false" | "t" | "f" | "1" | "0":
                    qs = qs.owned() if str2bool(owned) else qs.unowned()
                case _:
                    qs = qs.owned_by(owned)
        if want_to_read := request.GET.get("want_to_read"):
            qs = qs.filter(want_to_read=str2bool(want_to_read))
        if read := request.GET.get("read"):
            qs = qs.read() if str2bool(read) else qs.unread()

        return qs

    def filter_by_format(self, edition_format: str) -> "BookQuerySet":
        edition_format = edition_format.strip("s").upper()
        if edition_format == "PHYSICAL":
            return self.filter(
                Q(edition_format=Book.Format["PAPERBACK"])
                | Q(edition_format=Book.Format["HARDBACK"])
            )
        if edition_format == "EBOOK":
            return self.filter(
                Q(edition_format=Book.Format[edition_format])
                | Q(has_ebook_edition=True)
            )
        return self.filter(edition_format=Book.Format[edition_format])

    @property
    def page_count(self) -> int:
        if count := self.aggregate(Sum("page_count"))["page_count__sum"]:
            return int(count)
        return 0


BookManager = BaseBookManager.from_queryset(BookQuerySet)


class Book(TimestampedModel, SluggableModel, BookWithEditions):
    objects = BookManager()

    class Meta:
        indexes = [
            Index(fields=["series", "series_order", "title"]),
        ]
        ordering = [
            Lower("first_author__surname"),
            Lower("first_author__forenames"),
            "series",
            "series_order",
            "title",
        ]
        constraints = [
            CheckConstraint(
                check=(
                    Q(
                        # case one: both dates are set, so owner must not be set
                        acquired_date__isnull=False,
                        alienated_date__isnull=False,
                        owned_by__isnull=True,
                    )
                    | Q(
                        # case two: neither date is set, so owner must not be set
                        acquired_date__isnull=True,
                        alienated_date__isnull=True,
                        owned_by__isnull=True,
                    )
                    | Q(
                        # case three: acquired but not alienated so must have an owner
                        acquired_date__isnull=False,
                        alienated_date__isnull=True,
                        owned_by__isnull=False,
                    )
                    | Q(
                        # fallback case: neither date is set but might still be owned
                        acquired_date__isnull=True,
                        alienated_date__isnull=True,
                        owned_by__isnull=False,
                    )
                    | Q(
                        # default: neither date is set and it is not owned
                        acquired_date__isnull=True,
                        alienated_date__isnull=True,
                        owned_by__isnull=True,
                    )
                ),
                name="owned_dates_requires_owner",
            ),
            CheckConstraint(
                check=(
                    Q(owned_by__isnull=False, edition_format__ne=0)
                    | Q(owned_by__isnull=True, edition_format__gte=0)
                ),
                name="owned_must_have_format",
            ),
        ]

    title = models.CharField(db_index=True, max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    first_author = models.ForeignKey(
        Author, on_delete=models.CASCADE, null=True, related_name="first_authored_books"
    )
    first_author_role = models.CharField(
        db_index=True, max_length=255, blank=True, default=""
    )
    additional_authors = models.ManyToManyField(
        Author,
        through="BookAuthor",
        related_name="additional_authored_books",
        blank=True,
    )

    class Format(models.IntegerChoices):
        UNKNOWN = 0
        PAPERBACK = 1
        HARDBACK = 2
        EBOOK = 3
        WEB = 4

    first_published = models.PositiveSmallIntegerField(blank=True, default=0)
    language = models.CharField(max_length=2, default="en", choices=LANGUAGES)

    series = models.CharField(db_index=True, max_length=255, blank=True)
    series_order = models.FloatField(db_index=True, blank=True, default=0.0)

    # these at least in theory relate only to an edition, not every edition
    # edition could be a separate models but it would almost always be one-to-one
    edition_published = models.PositiveSmallIntegerField(blank=True, default=0)
    publisher = models.CharField(max_length=255, blank=True)
    edition_format = models.IntegerField(
        db_index=True, choices=Format.choices, default=0
    )
    edition_number = models.PositiveSmallIntegerField(blank=True, default=0)
    page_count = models.PositiveSmallIntegerField(blank=True, default=0)
    goodreads_id = models.CharField(max_length=255, blank=True)
    google_books_id = models.CharField(max_length=255, blank=True)
    isbn = models.CharField(max_length=13, blank=True)
    asin = models.CharField(max_length=255, blank=True)
    edition_language = models.CharField(
        max_length=2, blank=True, choices=LANGUAGES
    )  # i.e., a translation
    edition_title = models.CharField(max_length=255, blank=True)  # if translated
    edition_subtitle = models.CharField(max_length=255, blank=True)  # if translated

    acquired_date = models.DateField(blank=True, null=True)
    alienated_date = models.DateField(blank=True, null=True)
    was_borrowed = models.BooleanField(db_index=True, default=False)
    borrowed_from = models.CharField(max_length=255, blank=True)
    owned_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="owned_books",
    )

    image_url = models.URLField(blank=True)
    publisher_url = models.URLField(blank=True)

    want_to_read = models.BooleanField(db_index=True, default=True)

    review = models.TextField(blank=True)
    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        choices=[(i / 2, i / 2) for i in range(0, 11)],
        blank=True,
        default=0,
    )

    has_ebook_edition = models.BooleanField(default=False)
    ebook_isbn = models.CharField(max_length=13, blank=True)
    ebook_asin = models.CharField(max_length=255, blank=True)
    ebook_acquired_date = models.DateField(blank=True, null=True)

    parent_edition = models.ForeignKey(
        "self",
        related_name="subeditions",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    private = models.BooleanField(db_index=True, default=False)

    tags = models.ManyToManyField("Tag", related_name="books", blank=True)

    # derived properties

    @cached_property
    def authors(self) -> list[Author]:
        additional_authors = list(
            self.additional_authors.filter(
                bookauthor__role=self.first_author_role
            ).order_by("bookauthor__order")
        )
        if self.first_author:
            return [self.first_author, *additional_authors]
        return additional_authors

    @cached_property
    def all_authors(self) -> list[Author]:
        additional_authors = list(self.additional_authors.order_by("bookauthor__order"))
        if self.first_author:
            return [self.first_author, *additional_authors]
        return additional_authors

    @cached_property
    def all_authors_editors(self) -> bool:
        return len(self.authors) > 1 and all(
            author.is_editor_of(self) for author in self.all_authors
        )

    @property
    def all_log_entries(self) -> "models.QuerySet[LogEntry]":
        entries = self.log_entries.all()
        for edition in self.alternate_editions.all():
            entries |= edition.log_entries.all()
        return entries

    @property
    def ancestor_editions(self) -> list["Book"]:
        return (
            [self.parent_edition, *self.parent_edition.ancestor_editions]
            if self.parent_edition
            else []
        )

    @property
    def created_date_date(self) -> date:
        # for group-by
        return self.created_date.date()

    @property
    def currently_reading(self) -> bool:
        entries = self.log_entries.filter(end_date=None).order_by("-start_date")
        return bool(entries[0].currently_reading) if entries else False

    @property
    def display_date(self) -> str:
        if (
            self.edition_published
            and self.first_published
            and self.edition_published != self.first_published
        ):
            return f"[{self.first_published}] {self.edition_published}"
        if self.edition_published:
            return str(self.edition_published)
        return str(self.first_published) if self.first_published else "n.d."

    @property
    def display_details(self) -> str:
        result = ""

        if self.first_author_role != "editor":
            if len(self.authors) > 3:
                result = str(self.first_author) + " and others"
            else:
                result = oxford_comma([str(author) for author in self.authors])

            result += ", "

        result += (
            "_" + self.display_title.replace("_ ", r"\_ ").replace("*", r"\*") + "_"
        )

        if self.has_editors:
            result += ", ed. by "

            if len(self.editors) > 3:
                result += str(self.editors[0]) + " and others"
            else:
                result += oxford_comma(self.editors)

        if (
            self.alternate_editions.count()
            and self.edition_format
            and self.edition_title
            in self.alternate_editions.all().values_list("edition_title", flat=True)
        ):
            result += f", {self.get_edition_disambiguator()} edn."

        if self.publisher or self.edition_published or self.first_published:
            result += f" ({self.publisher + ', ' if self.publisher else ''}{self.edition_published or self.first_published})"

        return result

    @cached_property
    def display_series(self) -> str:
        if not self.series:
            return ""
        if self.subeditions.count() > 1 and all(
            book.series == self.series for book in self.subeditions.all()
        ):
            series_orders = sorted(book.series_order for book in self.subeditions.all())
            return f"{self.series}, #{str(min(series_orders)).replace('.0', '')}–{str(max(series_orders)).replace('.0', '')}"

        if self.series_order:
            return f"{self.series}, #{str(self.series_order).replace('.0', '')}"
        return self.series

    @cached_property
    def display_title(self) -> str:
        if self.edition_title:
            return self.edition_title + (
                f": {self.edition_subtitle}" if self.edition_subtitle else ""
            )
        return self.title + (": " + self.subtitle if self.subtitle else "")

    @property
    def ebook_url(self) -> str:
        return f"https://amazon.co.uk/dp/{self.ebook_asin}" if self.ebook_asin else ""

    @cached_property
    def editors(self) -> list[Author]:
        return [author for author in self.all_authors if author.is_editor_of(self)]

    @property
    def has_editors(self) -> bool:
        return len(self.editors) > 0

    @property
    def has_full_authors(self) -> bool:
        return len(self.authors) > 3 or self.authors != self.all_authors

    @property
    def has_original_title(self) -> bool:
        return (not self.edition_title) or self.title == self.edition_title

    @property
    def is_first_edition(self) -> bool:
        return (
            not self.edition_published
        ) or self.edition_published == self.first_published

    @property
    def is_translated(self) -> bool:
        return (
            self.edition_language is not None and self.edition_language != self.language
        )

    @property
    def isbn10(self) -> str:
        return isbn_to_isbn10(self.isbn)

    @property
    def modified_date_date(self) -> date:
        # for group-by
        return self.modified_date.date()

    @property
    def owned(self) -> bool:
        return (
            self.owned_by.username == "ben"
            if self.owned_by is not None
            else any(ancestor.owned for ancestor in self.ancestor_editions)
        )

    @property
    def owned_by_sara(self) -> bool:
        return (
            self.owned_by.username == "sara"
            if self.owned_by is not None
            else any(ancestor.owned_by_sara for ancestor in self.ancestor_editions)
        )

    @property
    def parent_owned(self) -> bool:
        return (not self.owned_by) and any(
            ancestor.owned for ancestor in self.ancestor_editions
        )

    @property
    def read(self) -> bool:
        if self.parent_edition and self.parent_edition.read:
            return True

        return (
            self.log_entries.filter(end_date__isnull=False, abandoned=False).count() > 0
        )

    @property
    def review_url(self) -> str:
        if self.review.startswith("http://") or self.review.startswith("https://"):
            return self.review.split()[0]
        return ""

    @property
    def search_query(self) -> str:
        return quote(
            f"{self.edition_title or self.title} {self.first_author and self.first_author.surname}"
        )

    @property
    def tags_list(self) -> set[str]:
        return {tag.name for tag in self.tags.all()}

    # methods

    def __str__(self) -> str:
        if not self.first_author or not self.display_title:
            return "<unknown>"

        result = f"{self.first_author}, {self.display_title}"

        if (
            self.alternate_editions.count()
            and self.edition_format
            and self.edition_title
            in self.alternate_editions.all().values_list("edition_title", flat=True)
        ):
            result += f" ({self.get_edition_disambiguator()} edition)"
        return result

    def add_author(
        self, author: "Author", role: str = "", order: int | None = None
    ) -> None:
        if author.id is not self.first_author_id and author not in self.authors:
            if not self.first_author:
                self.first_author = author
                self.first_author_role = role
                self.save()
            else:
                authorship = BookAuthor(
                    book=self, author=author, role=role, order=order
                )
                authorship.save()

            del self.authors

    def finish_reading(self) -> None:
        entry = self.log_entries.get(end_date=None)
        self.update_progress(percentage=100, page=self.page_count)
        entry.end_date = timezone.now()
        entry.save()

        if self.parent_edition:
            sibling_editions = self.parent_edition.subeditions
            if sibling_editions.count() == sibling_editions.read().count():
                self.parent_edition.finish_reading()

    def get_absolute_url(self) -> str:
        return reverse("library:book_details", args=[self.slug])

    def mark_owned(self) -> None:
        self.owned_by = User.objects.get(username="ben")
        self.acquired_date = timezone.now()
        self.was_borrowed = False
        self.borrowed_from = ""
        self.save()

    def mark_read_sometime(self) -> None:
        self.log_entries.create(
            start_date=None,
            end_date=timezone.datetime(1, 1, 1),  # type: ignore[attr-defined]
            end_precision=2,
        )

    def save(self, *args: Any, **kwargs: Any) -> None:
        if "goodreads" in self.image_url or "amazon" in self.image_url:
            self.image_url = re.sub(r"\._.+_\.jpg$", ".jpg", self.image_url)

        if not self.rating:
            self.rating = 0.0

        self.title = smarten(self.title)
        self.subtitle = smarten(self.subtitle)
        self.series = smarten(self.series)
        self.edition_title = smarten(self.edition_title)
        self.edition_subtitle = smarten(self.edition_subtitle)

        self.publisher = clean_publisher(self.publisher)

        if self.acquired_date and not self.alienated_date and not self.owned_by:
            self.owned_by = User.objects.get(username="ben")

        orig_goodreads_id = self.goodreads_id
        if self.id and (self.isbn or self.asin):
            old = Book.objects.get(pk=self.id)
            if self.isbn != old.isbn or self.asin != old.asin:
                self.goodreads_id = ""

        super().save(*args, **kwargs)

        verso.update(self)
        if any([self.asin, self.isbn, (self.title and self.first_author)]) and (
            not all([self.first_published, self.goodreads_id, self.image_url])
        ):
            goodreads.update(self)
            if orig_goodreads_id and not self.goodreads_id:
                self.goodreads_id = orig_goodreads_id
                super().save(*args, **kwargs)

        if any([self.isbn, self.google_books_id]) and (
            not all(
                [
                    self.google_books_id,
                    self.publisher,
                    self.page_count,
                    self.first_published,
                ]
            )
        ):
            google.update(self)
            verso.update(self)

        self.save_other_editions()
        self.subeditions.all().update(want_to_read=self.want_to_read)

    def _slug_fields(self) -> list[str]:
        fields = []
        if self.first_author:
            fields.append(self.first_author.surname)

        title = self.edition_title or self.title
        title = title.split(":")[0]

        title = remove_stopwords(title)

        fields.append(title)
        return fields

    def start_reading(self) -> None:
        if not self.log_entries.filter(end_date=None):
            self.log_entries.create()
            self.want_to_read = False
            self.save()

    def to_json(self) -> dict[str, Any]:
        fields = [
            "title",
            "subtitle",
            "first_author",
            "first_author_role",
            "edition_title",
            "edition_subtitle",
            "first_published",
            "language",
            "edition_published",
            "edition_language",
            "publisher",
            "edition_format",
            "edition_number",
            "page_count",
            "series",
            "series_order",
            "google_books_id",
            "goodreads_id",
            "isbn",
            "asin",
            "acquired_date",
            "alienated_date",
            "was_borrowed",
            "borrowed_from",
            "image_url",
            "publisher_url",
            "want_to_read",
            "owned_by",
            "review",
            "rating",
            "has_ebook_edition",
            "ebook_isbn",
            "ebook_asin",
            "ebook_acquired_date",
            "private",
            "parent_edition",
        ]
        result = {
            "id": self.id,
        }
        for field in fields:
            value = getattr(self, field, None)
            if value_id := getattr(self, field + "_id", None):
                result[field] = value_id
            elif value or (field == "want_to_read" and value is False):
                result[field] = value
        if self.tags:
            tags = flatten(((tag,), tag.parents_recursive) for tag in self.tags.all())

            result["tags"] = [tag.name for tag in flatten(tags)]
        if self.additional_authors.count():
            result["additional_authors"] = [
                (author.id, author.role_for_book(self) or None)
                for author in self.additional_authors.all()
            ]
        if self.log_entries.count():
            result["log_entries"] = [log.to_json() for log in self.log_entries.all()]

        if self.alternate_editions.count():
            primary_edition = self.alternate_editions.first()
            if (
                primary_edition
                and primary_edition != self
                and self.id < primary_edition.id
            ):
                result["primary_edition"] = primary_edition.id

        if self.reading_lists.count():
            result["reading_lists"] = [
                (
                    reading_list.title,
                    reading_list.readinglistentry_set.get(book=self).order
                    or list(
                        reading_list.readinglistentry_set.values_list("book", flat=True)
                    ).index(self.id),
                )
                for reading_list in self.reading_lists.all()
            ]

        return result

    def update(
        self, data: dict[str, str], force: bool = False  # noqa: FBT001, FBT002
    ) -> "Book":
        needs_save = False

        for key, value in data.items():
            if key == "id":
                continue

            if hasattr(self, key) and (force or not getattr(self, key)):
                if value != getattr(self, key):
                    needs_save = True
                setattr(self, key, value)

        if needs_save:
            self.save()
        return self

    def update_progress(
        self, percentage: float | None = None, page: int | None = None
    ) -> float:
        if not percentage:
            if not page:
                msg = "Must specify percentage or page"
                raise ValueError(msg)
            if not self.page_count:
                msg = "Must specify percentage when page count is unset"
                raise ValueError(msg)
            percentage = page / self.page_count * 100

        entry = self.log_entries.get(end_date=None)
        entry.progress_date = timezone.now()

        entry.progress_page = page or 0
        entry.progress_percentage = percentage
        entry.save()
        return percentage


class BookAuthor(TimestampedModel):
    class Meta:
        ordering = ["order"]
        unique_together = ("author", "book")

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    role = models.CharField(db_index=True, max_length=255, blank=True, default="")
    order = models.PositiveSmallIntegerField(db_index=True, blank=True, null=True)

    def __str__(self) -> str:
        return ": ".join([str(self.author), str(self.role), self.book.title])


class TagManager(models.Manager["Tag"]):
    def get(self, name: str) -> "Tag":
        tag, _ = Tag.objects.get_or_create(name=name.lower())
        return tag


class Tag(TimestampedModel):
    objects = TagManager()

    class Meta:
        ordering = ("name",)

    name = models.CharField(max_length=64, primary_key=True)
    parents = models.ManyToManyField(
        "self", related_name="children", blank=True, symmetrical=False
    )

    def __str__(self) -> str:
        return self.fullname

    @property
    def fullname(self) -> str:
        if parent := self.parents.first():
            return parent.fullname + " :: " + self.name
        return self.name

    @property
    def books_recursive(self) -> "BookQuerySet":
        books = self.books.distinct()
        for child in self.children.all():
            books |= child.books_recursive.distinct()
        return books

    @property
    def books_uniquely_tagged(self) -> "BookQuerySet":
        others = Tag.objects.exclude(name__in=[self.name, "fiction", "non-fiction"])
        return self.books_recursive.exclude(tags__in=others)

    @property
    def parents_recursive(self) -> models.QuerySet["Tag"]:
        return reduce(
            operator.or_,
            [p.parents_recursive for p in self.parents.all()],
            self.parents.all(),
        )

    @property
    def children_recursive(self) -> models.QuerySet["Tag"]:
        return reduce(
            operator.or_,
            [c.children_recursive for c in self.children.all()],
            self.children.all(),
        )

    @property
    def related(self) -> models.QuerySet["Tag"]:
        return reduce(
            operator.or_,
            [
                Tag.objects.filter(
                    name__in=[tag.name for tag in book.tags.all() if tag != self]
                )
                for book in self.books.all()
            ],
            Tag.objects.none(),
        )

    def __lt__(self, other: "Tag") -> bool:
        return self.name < other.name

    def get_absolute_url(self) -> str:
        return reverse("library:tag_details", args=[self.name])

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.name = self.name.lower()
        super().save(*args, **kwargs)
