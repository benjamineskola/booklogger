import re

from django.forms import (
    ModelForm,
    Select,
    SelectMultiple,
    ValidationError,
    inlineformset_factory,
)

from library.models import Author, Book, BookAuthor
from library.utils import isbn10_to_isbn


class AuthorWidget(Select):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({"class": "ui search selection dropdown"})


class TagWidget(SelectMultiple):
    def value_from_datadict(self, data, files, name):
        values = super().value_from_datadict(data, files, name)
        return ",".join(values)

    def optgroups(self, name, value, attrs=None):
        values = value[0].split(",") if value[0] else []
        selected = set(values)
        subgroup = [
            self.create_option(name, v, v, selected, i) for i, v in enumerate(values)
        ]
        return [(None, subgroup, 0)]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({"class": "ui search multiple selection dropdown"})
        tags = Book.objects.exclude(tags=[]).values_list("tags", flat=True)
        tags_choices = sorted(
            [
                {"name": i, "value": i}
                for i in set([item for sublist in tags for item in sublist])
            ],
            key=lambda i: i["name"],
        )
        self.values_dict = tags_choices


class AuthorForm(ModelForm):
    class Meta:
        model = Author
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(AuthorForm, self).__init__(*args, **kwargs)


class BookForm(ModelForm):
    class Meta:
        model = Book
        exclude = ["additional_authors", "created_date"]
        widgets = {
            "first_author": AuthorWidget,
            "tags": TagWidget,
        }

    def __init__(self, *args, **kwargs):
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

    def _clean_asin(self, asin):
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

    def clean_asin(self):
        return self._clean_asin(self.cleaned_data["asin"])

    def clean_ebook_asin(self):
        return self._clean_asin(self.cleaned_data["ebook_asin"])

    def clean_isbn(self):
        isbn = self.cleaned_data["isbn"]
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
        widgets = {"author": AuthorWidget}

    def __init__(self, *args, **kwargs):
        super(BookAuthorForm, self).__init__(*args, **kwargs)


BookAuthorFormSet = inlineformset_factory(Book, BookAuthor, form=BookAuthorForm,)
