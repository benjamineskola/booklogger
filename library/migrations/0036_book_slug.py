# Generated by Django 3.0.7 on 2020-06-30 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0035_auto_20200628_1543"),
    ]

    operations = [
        migrations.AddField(
            model_name="book", name="slug", field=models.SlugField(null=True),
        ),
    ]
