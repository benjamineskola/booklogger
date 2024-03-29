# Generated by Django 3.0.7 on 2020-07-05 10:31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def migrate_forwards(apps, schema_editor):
    Book = apps.get_model("library", "Book")
    User = apps.get_model("auth", "User")

    ben, _ = User.objects.get_or_create(username="ben")

    for book in Book.objects.filter(owned=True):
        book.owned_by = ben
        book.save()

    sara, _ = User.objects.get_or_create(username="sara")

    for book in Book.objects.filter(borrowed_from__iexact="sara"):
        book.borrowed_from = ""
        book.owned_by = sara
        book.save()


def migrate_backwards(apps, schema_editor):
    Book = apps.get_model("library", "Book")
    User = apps.get_model("auth", "User")

    ben, _ = User.objects.get_or_create(username="ben")

    for book in ben.owned_books.all():
        book.owned = True
        book.owned_by = None
        book.save()

    sara, _ = User.objects.get_or_create(username="sara")

    for book in sara.owned_books.all():
        book.borrowed_from = "sara"
        book.owned_by = None
        book.save()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("library", "0040_auto_20200703_1405"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="owned_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="owned_books",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(migrate_forwards, migrate_backwards),
        migrations.RemoveField(model_name="book", name="owned",),
    ]
