import re
from typing import Any

from django.forms import (
    ModelChoiceField,
    ModelForm,
    NumberInput,
    Select,
    SelectDateWidget,
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


class DateWidget(SelectDateWidget):
    def get_context(self, name: Any, value: Any, attrs: Any) -> dict[str, Any]:
        context = super().get_context(name, value, attrs)
        year_name = self.year_field % name
        year_widget = NumberInput(attrs).get_context(
            name=year_name,
            value=context["widget"]["value"]["year"],
            attrs={**context["widget"]["attrs"], "id": "id_%s" % year_name},
        )
        day_name = self.day_field % name
        day_widget = NumberInput(
            attrs,
        ).get_context(
            name=day_name,
            value=context["widget"]["value"]["day"],
            attrs={**context["widget"]["attrs"], "id": "id_%s" % day_name},
        )
        for i, subwidget in enumerate(context["widget"]["subwidgets"]):
            if subwidget["name"].endswith("_day"):
                context["widget"]["subwidgets"][i] = day_widget["widget"]
            if subwidget["name"].endswith("_year"):
                context["widget"]["subwidgets"][i] = year_widget["widget"]
        return context


class AuthorForm(ModelForm[Author]):
    class Meta:
        model = Author
        exclude = ["created_date", "modified_date"]


class AuthorField(ModelChoiceField):
    def to_python(self, value: str | None) -> Author | None:
        if not value:
            return None
        if value.isnumeric():
            return super().to_python(value)  # type: ignore[return-value]

        try:
            author, _ = Author.objects.get_or_create_by_single_name(value)
            return author  # noqa: TRY300
        except Exception as e:  # noqa: BLE001
            raise ValidationError(str(e)) from e


class BookForm(ModelForm[Book]):
    class Meta:
        model = Book
        exclude = ["additional_authors", "created_date", "modified_date"]
        field_classes = {"first_author": AuthorField}

        widgets = {
            "acquired_date": DateWidget(years=range(timezone.now().year + 1, 1986, -1)),
            "alienated_date": DateWidget(
                years=range(timezone.now().year + 1, 1986, -1)
            ),
            "ebook_acquired_date": DateWidget(
                years=range(timezone.now().year + 1, 2011, -1)
            ),
            "publisher": Select(choices=[("", "---------")]),
            "series": Select(choices=[("", "---------")]),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.fields["publisher"].widget.choices += [
            (publisher, publisher)
            for publisher in Book.objects.exclude(publisher="")
            .order_by("publisher")
            .values_list("publisher", flat=True)
            .distinct()
            if publisher
        ]
        self.fields["series"].widget.choices += [
            (series, series)
            for series in Book.objects.exclude(series="")
            .order_by("series")
            .values_list("series", flat=True)
            .distinct()
            if series
        ]
        self.fields["tags"].widget.choices = Tag.objects.values_list("name", "name")

        instance = kwargs.get("instance")
        if instance:
            qs = instance.first_author.books.exclude(pk=instance.id)

        if instance and qs.count() > 0:
            self.fields["alternate_editions"].queryset = qs  # type: ignore[attr-defined]
            self.fields["parent_edition"].queryset = qs  # type: ignore[attr-defined]
        else:
            del self.fields["alternate_editions"]
            del self.fields["parent_edition"]

        for field in self.fields.values():
            if getattr(field.widget, "input_type", None) == "number":
                field.widget.input_type = "text"
                field.widget.attrs["inputmode"] = "numeric"
                field.widget.attrs["pattern"] = "[0-9.]*"

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

            msg = "Not a valid ASIN or Amazon URL"
            raise ValidationError(msg)
        return asin

    def clean_asin(self) -> str:
        return self._clean_asin(self.cleaned_data["asin"])

    def clean_ebook_asin(self) -> str:
        return self._clean_asin(self.cleaned_data["ebook_asin"])

    def clean_isbn(self) -> str:
        isbn: str = self.cleaned_data["isbn"]
        if not isbn:
            return ""
        if isbn := isbn10_to_isbn(isbn):
            return isbn

        msg = "Not a valid ISBN-13, ISBN-10, or SBN"
        raise ValidationError(msg)


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


BulkBookFormSet: type = modelformset_factory(
    Book,
    fields=[
        "title",
        "first_author",
        "series",
        "series_order",
        "edition_format",
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
