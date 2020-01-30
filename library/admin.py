from django.contrib import admin
from django.db import models

from .models import Author, Book, BookAuthor, LogEntry

# Register your models here.


class BookAuthorInline(admin.TabularInline):
    model = BookAuthor
    extra = 1


class BookAdmin(admin.ModelAdmin):
    inlines = (BookAuthorInline,)


admin.site.register(Author)
admin.site.register(Book, BookAdmin)
admin.site.register(BookAuthor)
admin.site.register(LogEntry)
