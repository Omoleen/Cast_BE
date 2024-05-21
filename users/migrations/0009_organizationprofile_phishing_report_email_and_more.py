# Generated by Django 4.1.7 on 2024-04-26 15:42

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "users",
            "0008_rename_campaign_email_notifiction_organizationprofile_campaign_email_notification",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="organizationprofile",
            name="phishing_report_email",
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.CreateModel(
            name="AuthorizedDomain",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now=True)),
                ("updated_at", models.DateTimeField(auto_now_add=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("domain", models.EmailField(max_length=254)),
                ("verified_on", models.DateTimeField(null=True)),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="authorized_domains",
                        to="users.organization",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
    ]