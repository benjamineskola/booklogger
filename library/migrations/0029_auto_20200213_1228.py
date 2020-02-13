# Generated by Django 3.0.2 on 2020-02-13 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0028_auto_20200210_0817'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='rating',
            field=models.DecimalField(blank=True, choices=[(0.5, 0.5), (1.0, 1.0), (1.5, 1.5), (2.0, 2.0), (2.5, 2.5), (3.0, 3.0), (3.5, 3.5), (4.0, 4.0), (4.5, 4.5), (5.0, 5.0)], decimal_places=1, max_digits=2, null=True),
        ),
        migrations.AddField(
            model_name='book',
            name='review',
            field=models.TextField(blank=True),
        ),
    ]
