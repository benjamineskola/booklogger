import re

from django.forms import Form, ModelForm, ValidationError
from django_select2 import forms as s2forms

from library.models import Author, Book, BookAuthor


class AuthorWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "surname__icontains",
        "forenames__icontains",
        "preferred_forenames__icontains",
    ]


class TagWidget(s2forms.Select2TagWidget):
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


class BootstrapForm(Form):
    def __init__(self, *args, **kwargs):
        super(BootstrapForm, self).__init__(*args, **kwargs)
        for field_name in self.fields:
            field = self.fields[field_name]
            widget = field.widget
            widget.attrs.update({"class": "form-control"})
            if widget.__class__.__name__ == "CheckboxInput":
                widget.attrs["class"] += " col-1"
            elif widget.__class__.__name__ == "Select":
                widget.attrs["class"] += " custom-select"

            if field.required:
                field.label_suffix = " (required):"

        for field_name in self.errors:
            self.fields[field_name].widget.attrs["class"] += " is-invalid"

    def set_delete_classes(self):
        self.fields["DELETE"].widget.attrs.update({"class": "form-control"})


class BootstrapModelForm(BootstrapForm, ModelForm):
    def __init__(self, *args, **kwargs):
        super(BootstrapModelForm, self).__init__(*args, **kwargs)


class AuthorForm(BootstrapModelForm):
    class Meta:
        model = Author
        fields = "__all__"
        widgets = {
            "primary_language": s2forms.Select2Widget,
        }

    def __init__(self, *args, **kwargs):
        super(AuthorForm, self).__init__(*args, **kwargs)


class BookForm(BootstrapModelForm):
    class Meta:
        model = Book
        exclude = ["additional_authors", "created_date"]
        widgets = {
            "edition_language": s2forms.Select2Widget,
            "first_author": AuthorWidget,
            "language": s2forms.Select2Widget,
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
        if (
            len(isbn) not in [9, 10, 13]
            or not isbn[0:-1].isnumeric()
            or (not isbn[-1].isnumeric() and isbn[-1].upper() != "X")
        ):
            raise ValidationError("Not a valid ISBN-13, ISBN-10, or SBN")
        elif len(isbn) == 13:
            return isbn
        else:
            if len(isbn) == 9:
                # let's assume it's a pre-ISBN SBN
                isbn = "0" + isbn

            isbn = "978" + isbn
            ints = [int(c) for c in isbn[0:-1]]

            checksum = 0
            for i, j in enumerate(ints):
                if i % 2 == 0:
                    checksum += j
                else:
                    checksum += j * 3
            checksum = 10 - checksum % 10

            return "".join([str(c) for c in ints] + [str(checksum)])


class BookAuthorForm(BootstrapModelForm):
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
