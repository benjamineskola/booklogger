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
)
from django.utils import timezone

from library.models import (  # type: ignore [attr-defined]
    Author,
    Book,
    BookAuthor,
    LogEntry,
    ReadingList,
    ReadingListEntry,
    Tag,
)
from library.utils import isbn10_to_isbn


class AuthorForm(ModelForm):
    class Meta:
        model = Author
        exclude = ["created_date", "modified_date"]

    def __init__(self, *args: Any, **kwargs: Any):
        super(AuthorForm, self).__init__(*args, **kwargs)


class AuthorField(ModelChoiceField):
    def to_python(self, value: Optional[str]) -> Author:
        if value and value.isnumeric():
            return super().to_python(value)
        else:
            try:
                author, _ = Author.objects.get_or_create_by_single_name(value)
                return author
            except Exception as e:
                raise ValidationError(str(e))


class BookForm(ModelForm):
    class Meta:
        model = Book
        exclude = ["additional_authors", "created_date", "modified_date"]
        field_classes = {"first_author": AuthorField}
        widgets = {
            "acquired_date": SelectDateWidget(
                years=range(
                    Book.objects.order_by("acquired_date").first().acquired_date.year,
                    timezone.now().year + 1,
                )
            ),
            "alienated_date": SelectDateWidget(
                years=range(
                    Book.objects.order_by("alienated_date").first().alienated_date.year,
                    timezone.now().year + 1,
                )
            ),
            "ebook_acquired_date": SelectDateWidget(
                years=range(2011, timezone.now().year + 1)
            ),
            "publisher": Select(
                choices=[("", "---------")]
                + list(
                    Book.objects.exclude(publisher="")
                    .order_by("publisher")
                    .values_list("publisher", "publisher")
                    .distinct("publisher")
                )
            ),
            "tags": SelectMultiple(choices=Tag.objects.values_list("name", "name")),
        }

    def __init__(self, *args: Any, **kwargs: Any):
        super(BookForm, self).__init__(*args, **kwargs)

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
            else:
                raise ValidationError("Not a valid ASIN or Amazon URL")
                return asin
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


class BookAuthorForm(ModelForm):
    class Meta:
        model = BookAuthor
        fields = [
            "author",
            "role",
            "order",
        ]
        field_classes = {"author": AuthorField}

    def __init__(self, *args: Any, **kwargs: Any):
        super(BookAuthorForm, self).__init__(*args, **kwargs)


class LogEntryForm(ModelForm):
    class Meta:
        model = BookAuthor
        exclude = ["created_date", "modified_date"]


class ReadingListForm(ModelForm):
    class Meta:
        model = ReadingList
        fields = ["title", "books"]


class ReadingListEntryForm(ModelForm):
    class Meta:
        model = ReadingListEntry
        fields = ["reading_list", "order"]


BookAuthorFormSet = inlineformset_factory(
    Book, BookAuthor, form=BookAuthorForm, extra=0
)
LogEntryFormSet = inlineformset_factory(Book, LogEntry, form=LogEntryForm, extra=0)
ReadingListEntryFormSet = inlineformset_factory(
    Book, ReadingListEntry, ReadingListEntryForm, extra=0
)
