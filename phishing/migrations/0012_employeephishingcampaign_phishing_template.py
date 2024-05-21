# Generated by Django 4.1.7 on 2024-05-08 12:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("phishing", "0011_remove_phishingcampaign_phishing_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="employeephishingcampaign",
            name="phishing_template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="employee_records",
                to="phishing.phishingtemplate",
            ),
        ),
    ]
