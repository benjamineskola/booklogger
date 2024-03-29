# Generated by Django 3.0.2 on 2020-02-23 12:19

import django.db.models.functions.text
from django.db import migrations, models


def single_name_to_surname(apps, schema_editor):
    Author = apps.get_model("library", "Author")

    for author in Author.objects.exclude(single_name=""):
        author.surname = author.single_name
        author.single_name = ""
        author.save()


def surname_to_single_name(apps, schema_editor):
    Author = apps.get_model("library", "Author")

    for author in Author.objects.filter(forenames=""):
        author.single_name = author.surname
        author.surname = ""
        author.save()


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0033_auto_20200222_1819"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="author",
            options={
                "ordering": [
                    django.db.models.functions.text.Lower("surname"),
                    django.db.models.functions.text.Lower("forenames"),
                ]
            },
        ),
        migrations.RemoveConstraint(
            model_name="author", name="surname_and_forenames_or_single_name",
        ),
        migrations.RunPython(single_name_to_surname, surname_to_single_name),
        migrations.RemoveField(model_name="author", name="single_name",),
        migrations.AddField(
            model_name="author",
            name="surname_first",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="author",
            name="surname",
            field=models.CharField(db_index=True, max_length=255),
        ),
    ]
