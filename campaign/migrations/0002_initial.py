# Generated by Django 4.1.7 on 2024-04-08 16:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0001_initial"),
        ("campaign", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="departments",
            field=models.ManyToManyField(
                blank=True, related_name="campaigns", to="users.department"
            ),
        ),
        migrations.AddField(
            model_name="campaign",
            name="employees",
            field=models.ManyToManyField(
                blank=True, related_name="emp_campaigns", to="users.employee"
            ),
        ),
        migrations.AddField(
            model_name="campaign",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="org_campaigns",
                to="users.organization",
            ),
        ),
    ]
