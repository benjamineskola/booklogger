from django.contrib import admin

from .models import (
    ApiKey,
    Author,
    Book,
    BookAuthor,
    LogEntry,
    Queue,
    ReadingList,
    ReadingListEntry,
    Tag,
)

# Register your models here.


class ApiKeyAdmin(admin.ModelAdmin[ApiKey]):
    search_fields = ["user", "key"]
    readonly_fields = ("created_date", "modified_date")


class AuthorAdmin(admin.ModelAdmin[Author]):
    search_fields = ["surname", "forenames"]
    readonly_fields = ("created_date", "modified_date")


class BookAuthorInline(admin.TabularInline[BookAuthor, Book]):
    autocomplete_fields = ["author", "book"]
    model = BookAuthor
    extra = 1
    readonly_fields = ("created_date", "modified_date")


class LogEntryAdmin(admin.ModelAdmin[LogEntry]):
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
    readonly_fields = ("created_date", "modified_date")


class LogEntryInline(admin.TabularInline[LogEntry, Book]):
    model = LogEntry
    extra = 0
    readonly_fields = ("created_date", "modified_date")


class BookAdmin(admin.ModelAdmin[Book]):
    autocomplete_fields = ["first_author", "editions"]
    inlines = (BookAuthorInline, LogEntryInline)
    readonly_fields = ("created_date", "modified_date")
    search_fields = [
        "title",
        "series",
        "tags__name",
        "edition_title",
        "first_author__surname",
        "first_author__forenames",
        "additional_authors__surname",
        "additional_authors__forenames",
    ]


class ReadingListEntryInline(admin.TabularInline[ReadingListEntry, Book]):
    model = ReadingListEntry
    autocomplete_fields = ("book",)
    readonly_fields = ("created_date", "modified_date")


class ReadingListAdmin(admin.ModelAdmin[ReadingList]):
    readonly_fields = ("created_date", "modified_date")
    inlines = (ReadingListEntryInline,)


admin.site.register(ApiKey, ApiKeyAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(BookAuthor)
admin.site.register(LogEntry, LogEntryAdmin)
admin.site.register(Tag)
admin.site.register(ReadingList, ReadingListAdmin)
admin.site.register(Queue)
