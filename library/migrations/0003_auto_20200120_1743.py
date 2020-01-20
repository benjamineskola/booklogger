# Generated by Django 3.0.2 on 2020-01-20 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0002_auto_20200120_1548'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='series',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='book',
            name='series_order',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='book',
            name='edition_format',
            field=models.IntegerField(blank=True, choices=[(1, 'Paperback'), (2, 'Hardback'), (3, 'Ebook'), (4, 'Web')]),
        ),
    ]
