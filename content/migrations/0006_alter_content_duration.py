# Generated by Django 4.1.7 on 2024-04-18 12:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0005_merge_20240417_1039"),
    ]

    operations = [
        migrations.AlterField(
            model_name="content",
            name="duration",
            field=models.DurationField(blank=True, null=True),
        ),
    ]