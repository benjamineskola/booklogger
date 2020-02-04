# Generated by Django 3.0.2 on 2020-02-04 13:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0019_auto_20200203_2157'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='additional_authors',
            field=models.ManyToManyField(related_name='additional_authored_books', through='library.BookAuthor', to='library.Author'),
        ),
        migrations.AlterField(
            model_name='book',
            name='first_author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='first_authored_books', to='library.Author'),
        ),
    ]
