# Generated by Django 3.0.2 on 2020-01-24 12:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0006_auto_20200123_1620'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookauthor',
            name='role',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
