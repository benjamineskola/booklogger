# Generated by Django 3.1.4 on 2020-12-10 17:30

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0055_auto_20201206_1306'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReadingList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(db_index=True, max_length=255)),
                ('created_date', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('modified_date', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='ReadingListEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveSmallIntegerField(blank=True, db_index=True, null=True)),
                ('created_date', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('modified_date', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='library.book')),
                ('reading_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='library.readinglist')),
            ],
            options={
                'ordering': ['order'],
                'unique_together': {('reading_list', 'book')},
            },
        ),
        migrations.AddField(
            model_name='readinglist',
            name='books',
            field=models.ManyToManyField(blank=True, related_name='reading_lists', through='library.ReadingListEntry', to='library.Book'),
        ),
    ]
