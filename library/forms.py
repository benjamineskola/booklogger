import re
from typing import Any, Optional

from django.forms import (
    ModelChoiceField,
    ModelForm,
    Select,
    SelectDateWidget,
    SelectMultiple,
    ValidationError,
    inlineformset_factory,
    modelformset_factory,
)
from django.utils import timezone

from library.models import (
    Author,
    Book,
    BookAuthor,
    LogEntry,
    ReadingList,
    ReadingListEntry,
    Tag,
)
from library.utils import isbn10_to_isbn


class AuthorForm(ModelForm[Author]):
    class Meta:
        model = Author
        exclude = ["created_date", "modified_date"]


class AuthorField(ModelChoiceField):
    def to_python(self, value: Optional[str]) -> Optional[Author]:
        if not value:
            return None
        if value.isnumeric():
            return super().to_python(value)

        try:
            author, _ = Author.objects.get_or_create_by_single_name(value)
            return author
        except Exception as e:
            raise ValidationError(str(e)) from e


class BookForm(ModelForm[Book]):
    class Meta:
        model = Book
        exclude = ["additional_authors", "created_date", "modified_date"]
        field_classes = {"first_author": AuthorField}

        widgets = {
            "acquired_date": SelectDateWidget(
                years=range(timezone.now().year + 1, 1986, -1)
            ),
            "alienated_date": SelectDateWidget(
                years=range(timezone.now().year + 1, 1986, -1)
            ),
            "ebook_acquired_date": SelectDateWidget(
                years=range(timezone.now().year + 1, 2011, -1)
            ),
            "publisher": Select(choices=[("", "---------")]),
            "series": Select(choices=[("", "---------")]),
            "tags": SelectMultiple(),
        }

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.fields["publisher"].widget.choices += [
            (publisher, publisher)
            for publisher in Book.objects.exclude(publisher="")
            .order_by("publisher")
            .values_list("publisher", flat=True)
            .distinct("publisher")
            if publisher
        ]
        self.fields["series"].widget.choices += [
            (series, series)
            for series in Book.objects.exclude(series="")
            .order_by("series")
            .values_list("series", flat=True)
            .distinct("series")
            if series
        ]
        self.fields["tags"].widget.choices = Tag.objects.values_list("name", "name")

        instance = kwargs.get("instance")
        if instance:
            qs = instance.first_author.books.exclude(pk=instance.id)

        if instance and qs.count() > 0:
            self.fields["editions"].queryset = qs
            self.fields["parent_edition"].queryset = qs
        else:
            del self.fields["editions"]
            del self.fields["parent_edition"]

    def _clean_asin(self, asin: str) -> str:
        if not asin:
            return ""
        if len(asin) != 10:
            if (
                asin.startswith("http")
                and "amazon" in asin
                and (matches := re.search(r"/(?:gp/product|dp)/([^/]+)/", asin))
            ):
                return matches[1]

            raise ValidationError("Not a valid ASIN or Amazon URL")
        return asin

    def clean_asin(self) -> str:
        return self._clean_asin(self.cleaned_data["asin"])

    def clean_ebook_asin(self) -> str:
        return self._clean_asin(self.cleaned_data["ebook_asin"])

    def clean_isbn(self) -> str:
        isbn: str = self.cleaned_data["isbn"]
        if not isbn:
            return ""
        isbn = isbn10_to_isbn(isbn)
        if not isbn:
            raise ValidationError("Not a valid ISBN-13, ISBN-10, or SBN")
        return isbn


class BookAuthorForm(ModelForm[BookAuthor]):
    class Meta:
        model = BookAuthor
        fields = [
            "author",
            "role",
            "order",
        ]
        field_classes = {"author": AuthorField}


class LogEntryForm(ModelForm[LogEntry]):
    class Meta:
        model = LogEntry
        exclude = ["created_date", "modified_date"]


class ReadingListForm(ModelForm[ReadingList]):
    class Meta:
        model = ReadingList
        fields = ["title", "books"]


class ReadingListEntryForm(ModelForm[ReadingListEntry]):
    class Meta:
        model = ReadingListEntry
        fields = ["reading_list", "order"]


BulkBookFormSet = modelformset_factory(
    Book,
    fields=[
        "title",
        "first_author",
        "series",
        "series_order",
        "edition_format",
        "tags",
    ],
    extra=0,
)
BookAuthorFormSet = inlineformset_factory(
    Book, BookAuthor, form=BookAuthorForm, extra=0
)
LogEntryFormSet = inlineformset_factory(Book, LogEntry, form=LogEntryForm, extra=0)
ReadingListEntryFormSet = inlineformset_factory(
    Book, ReadingListEntry, ReadingListEntryForm, extra=0
)
