from django.forms import ModelForm

from library.models import Book


class BookForm(ModelForm):
    class Meta:
        model = Book
        exclude = ["created_date"]

    def __init__(self, *args, **kwargs):
        super(BookForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "form-control col-8"})
