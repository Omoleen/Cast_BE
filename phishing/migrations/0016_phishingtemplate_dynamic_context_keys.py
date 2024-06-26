# Generated by Django 4.1.7 on 2024-05-20 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("phishing", "0015_phishingtemplate_landing_page_css_styles"),
    ]

    operations = [
        migrations.AddField(
            model_name="phishingtemplate",
            name="dynamic_context_keys",
            field=models.JSONField(
                blank=True,
                default=list,
                null=True,
                verbose_name="Randomly generated fields during phishing campaign",
            ),
        ),
    ]
