from django.contrib import admin
from django.db import models

from .models import Author, Book, BookAuthor, LogEntry

# Register your models here.


class BookAuthorInline(admin.TabularInline):
    model = BookAuthor
    extra = 1


class AuthorAdmin(admin.ModelAdmin):
    inlines = (BookAuthorInline,)


class BookAdmin(admin.ModelAdmin):
    inlines = (BookAuthorInline,)


admin.site.register(Author, AuthorAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(BookAuthor)
admin.site.register(LogEntry)
