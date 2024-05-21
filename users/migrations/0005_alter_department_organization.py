# Generated by Django 4.1.7 on 2024-04-26 14:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_organizationprofile_cut_off_score"),
    ]

    operations = [
        migrations.AlterField(
            model_name="department",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="departments",
                to="users.organization",
            ),
        ),
    ]
