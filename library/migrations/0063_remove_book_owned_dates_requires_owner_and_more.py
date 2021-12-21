# Generated by Django 4.0 on 2021-12-21 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0062_logentry_abandoned'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='book',
            name='owned_dates_requires_owner',
        ),
        migrations.AlterField(
            model_name='book',
            name='editions',
            field=models.ManyToManyField(blank=True, to='library.Book'),
        ),
        migrations.AddConstraint(
            model_name='book',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('acquired_date__isnull', False), ('alienated_date__isnull', False), ('owned_by__isnull', True)), models.Q(('acquired_date__isnull', True), ('alienated_date__isnull', True), ('owned_by__isnull', True)), models.Q(('acquired_date__isnull', False), ('alienated_date__isnull', True), ('owned_by__isnull', False)), models.Q(('acquired_date__isnull', True), ('alienated_date__isnull', True), ('owned_by__isnull', False)), models.Q(('acquired_date__isnull', True), ('alienated_date__isnull', True), ('owned_by__isnull', True)), _connector='OR'), name='owned_dates_requires_owner'),
        ),
    ]
