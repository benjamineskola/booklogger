from django.contrib import admin

from .models import Author, Book, BookAuthor, LogEntry

# Register your models here.


admin.site.register(Author)
admin.site.register(Book)
admin.site.register(BookAuthor)
admin.site.register(LogEntry)
