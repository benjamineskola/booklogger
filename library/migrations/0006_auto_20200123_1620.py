# Generated by Django 3.0.2 on 2020-01-23 16:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0005_auto_20200120_2111'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='bookauthor',
            unique_together={('author', 'book')},
        ),
    ]
