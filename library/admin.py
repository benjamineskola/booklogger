from django.contrib import admin

from .models import (
    Author,
    Book,
    BookAuthor,
    LogEntry,
    ReadingList,
    ReadingListEntry,
    Tag,
)

# Register your models here.


class AuthorAdmin(admin.ModelAdmin):
    search_fields = ["surname", "forenames"]


class BookAuthorInline(admin.TabularInline):
    autocomplete_fields = ["author", "book"]
    model = BookAuthor
    extra = 1


class LogEntryAdmin(admin.ModelAdmin):
    autocomplete_fields = ["book"]
    search_fields = [
        "book__title",
        "book__series",
        "book__tags",
        "book__edition_title",
        "book__first_author__surname",
        "book__first_author__forenames",
        "book__additional_authors__surname",
        "book__additional_authors__forenames",
    ]


class LogEntryInline(admin.TabularInline):
    model = LogEntry
    extra = 0


class BookAdmin(admin.ModelAdmin):
    autocomplete_fields = ["first_author", "editions"]
    inlines = (BookAuthorInline, LogEntryInline)
    readonly_fields = ("created_date",)
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


class ReadingListEntryInline(admin.TabularInline):
    model = ReadingListEntry
    autocomplete_fields = ("book",)


class ReadingListAdmin(admin.ModelAdmin):
    readonly_fields = ("created_date", "modified_date")
    inlines = (ReadingListEntryInline,)


admin.site.register(Author, AuthorAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(BookAuthor)
admin.site.register(LogEntry, LogEntryAdmin)
admin.site.register(Tag)
admin.site.register(ReadingList, ReadingListAdmin)
