# Generated by Django 3.0.7 on 2020-07-23 14:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0047_auto_20200716_0953'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='primary_identity',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pseudonyms', to='library.Author'),
        ),
    ]