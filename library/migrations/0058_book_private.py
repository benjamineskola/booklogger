# Generated by Django 3.2.7 on 2021-10-21 15:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0057_logentry_exclude_from_stats'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='private',
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
