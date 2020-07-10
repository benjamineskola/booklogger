from django.forms import ModelForm

from library.models import Author, Book


class AuthorForm(ModelForm):
    class Meta:
        model = Author
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(AuthorForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "form-control col-8"})


class BookForm(ModelForm):
    class Meta:
        model = Book
        exclude = ["additional_authors", "created_date"]

    def __init__(self, *args, **kwargs):
        super(BookForm, self).__init__(*args, **kwargs)
        if "instance" in kwargs:
            self.fields["editions"].queryset = Book.objects.filter(
                first_author=kwargs["instance"].first_author
            )
            self.fields["parent_edition"].queryset = Book.objects.filter(
                first_author=kwargs["instance"].first_author
            )
        else:
            self._meta.exclude += "editions"

        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "form-control col-8"})
