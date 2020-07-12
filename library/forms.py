from django.forms import ModelForm

from library.models import Author, Book


class AuthorForm(ModelForm):
    class Meta:
        model = Author
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(AuthorForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            widget = self.fields[field].widget
            widget.attrs.update({"class": "form-control"})
            if widget.__class__.__name__ == "CheckboxInput":
                widget.attrs["class"] += " col-1"
            else:
                widget.attrs["class"] += " col-8"


class BookForm(ModelForm):
    class Meta:
        model = Book
        exclude = ["additional_authors", "created_date"]

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

        for field in self.fields:
            widget = self.fields[field].widget
            widget.attrs.update({"class": "form-control"})
            if widget.__class__.__name__ == "CheckboxInput":
                widget.attrs["class"] += " col-1"
