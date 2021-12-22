# Generated by Django 4.0 on 2021-12-22 13:40

from django.db import migrations, models


def forwards_func(apps, schema_editor):
    Book = apps.get_model("library", "Book")
    db_alias = schema_editor.connection.alias
    Book.objects.using(db_alias).filter(edition_number__isnull=True).update(
        edition_number=0
    )
    Book.objects.using(db_alias).filter(edition_published__isnull=True).update(
        edition_published=0
    )
    Book.objects.using(db_alias).filter(first_published__isnull=True).update(
        first_published=0
    )
    Book.objects.using(db_alias).filter(page_count__isnull=True).update(page_count=0)
    Book.objects.using(db_alias).filter(series_order__isnull=True).update(
        series_order=0
    )


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0063_remove_book_owned_dates_requires_owner_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
