from django.contrib import admin
from django.db import models

from .models import Author, Book, BookAuthor, LogEntry

# Register your models here.


class AuthorAdmin(admin.ModelAdmin):
    search_fields = ["surname", "forenames"]


class BookAuthorInline(admin.TabularInline):
    autocomplete_fields = ["author", "book"]
    model = BookAuthor
    extra = 1


class LogEntryInline(admin.TabularInline):
    model = LogEntry
    extra = 0


class BookAdmin(admin.ModelAdmin):
    autocomplete_fields = ["first_author"]
    inlines = (BookAuthorInline, LogEntryInline)
    search_fields = [
        "title",
        "series",
        "tags",
        "edition_title",
        "first_author__surname",
        "first_author__forenames",
        "additional_authors__surname",
        "additional_authors__forenames",
    ]


admin.site.register(Author, AuthorAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(BookAuthor)
admin.site.register(LogEntry)
