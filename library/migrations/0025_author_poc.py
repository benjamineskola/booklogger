# Generated by Django 3.0.2 on 2020-02-08 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0024_auto_20200208_1145'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='poc',
            field=models.BooleanField(default=False),
        ),
    ]
