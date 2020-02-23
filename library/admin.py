from django.contrib import admin
from django.db import models

from .models import Author, Book, BookAuthor, LogEntry

# Register your models here.


class AuthorAdmin(admin.ModelAdmin):
    search_fields = ["surname", "forenames", "single_name"]


class BookAuthorInline(admin.TabularInline):
    autocomplete_fields = ["author", "book"]
    model = BookAuthor
    extra = 1


class LogEntryAdmin(admin.ModelAdmin):
    autocomplete_fields = ["book"]
    search_fields = [
        "book_title",
        "book_series",
        "book_tags",
        "book_edition_title",
        "book_first_author__surname",
        "book_first_author__forenames",
        "book_first_author__single_name",
        "book_additional_authors__surname",
        "book_additional_authors__forenames",
        "book_additional_authors__single_name",
    ]


class LogEntryInline(admin.TabularInline):
    model = LogEntry
    extra = 0


class BookAdmin(admin.ModelAdmin):
    autocomplete_fields = ["first_author", "editions"]
    inlines = (BookAuthorInline, LogEntryInline)
    search_fields = [
        "title",
        "series",
        "tags",
        "edition_title",
        "first_author__surname",
        "first_author__forenames",
        "first_author__single_name",
        "additional_authors__surname",
        "additional_authors__forenames",
        "additional_authors__single_name",
    ]


admin.site.register(Author, AuthorAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(BookAuthor)
admin.site.register(LogEntry, LogEntryAdmin)
