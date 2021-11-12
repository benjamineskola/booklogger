# Generated by Django 3.2.7 on 2021-11-04 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0058_book_private'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='book',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('acquired_date__isnull', False), ('alienated_date__isnull', False), ('owned_by__isnull', True)), models.Q(('acquired_date__isnull', True), ('alienated_date__isnull', True), ('owned_by__isnull', True)), models.Q(('acquired_date__isnull', False), ('alienated_date__isnull', True), ('owned_by__isnull', False)), models.Q(('acquired_date__isnull', True), ('alienated_date__isnull', True), ('owned_by__isnull', False)), _connector='OR'), name='owned_dates_requires_owner'),
        ),
    ]