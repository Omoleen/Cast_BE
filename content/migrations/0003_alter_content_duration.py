# Generated by Django 4.1.7 on 2024-04-15 10:31

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="content",
            name="duration",
            field=models.DurationField(
                blank=True, default=datetime.timedelta(0), null=True
            ),
        ),
    ]
