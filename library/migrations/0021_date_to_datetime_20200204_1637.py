# Generated by Django 3.0.2 on 2020-02-04 16:37

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0020_auto_20200204_1355'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logentry',
            name='end_date',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='logentry',
            name='progress_date',
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='logentry',
            name='start_date',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True),
        ),
    ]
