# Generated by Django 4.0.4 on 2022-05-05 10:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0066_alter_author_primary_language_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='edition_number',
            field=models.PositiveSmallIntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='book',
            name='edition_published',
            field=models.PositiveSmallIntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='book',
            name='first_published',
            field=models.PositiveSmallIntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='book',
            name='page_count',
            field=models.PositiveSmallIntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='book',
            name='series_order',
            field=models.FloatField(blank=True, db_index=True, default=0.0),
        ),
    ]
