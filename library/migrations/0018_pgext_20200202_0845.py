from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0017_auto_20200131_1910"),
    ]

    operations = [TrigramExtension()]
