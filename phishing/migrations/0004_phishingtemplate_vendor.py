# Generated by Django 4.1.7 on 2024-04-17 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("phishing", "0003_phishingcampaign_employees"),
    ]

    operations = [
        migrations.AddField(
            model_name="phishingtemplate",
            name="vendor",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
