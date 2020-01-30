# Generated by Django 3.0.2 on 2020-01-30 10:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0012_auto_20200130_1011'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='edition_format',
            field=models.IntegerField(blank=True, choices=[(1, 'Paperback'), (2, 'Hardback'), (3, 'Ebook'), (4, 'Web')], db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='book',
            name='owned',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='book',
            name='want_to_read',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='book',
            name='was_borrowed',
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
