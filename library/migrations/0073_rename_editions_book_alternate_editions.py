# Generated by Django 4.2 on 2023-07-14 12:19

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0072_apikey"),
    ]

    operations = [
        migrations.RenameField(
            model_name="book",
            old_name="editions",
            new_name="alternate_editions",
        ),
    ]
