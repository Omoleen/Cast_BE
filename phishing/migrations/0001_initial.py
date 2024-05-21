# Generated by Django 4.1.7 on 2024-04-08 16:03

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PhishingCampaign",
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
                (
                    "phishing_snapshot",
                    models.JSONField(blank=True, default=dict, null=True),
                ),
                (
                    "email_delivery_type",
                    models.CharField(
                        choices=[
                            ("immediately", "Immediately"),
                            ("scheduled", "Scheduled"),
                            ("scheduled_range", "Scheduled Range"),
                        ],
                        default="immediately",
                        max_length=256,
                    ),
                ),
                (
                    "email_delivery_date",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Email Delivery Date"
                    ),
                ),
                (
                    "email_delivery_start_date",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Email Delivery Start Date"
                    ),
                ),
                (
                    "email_delivery_end_date",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Email Delivery Start Date"
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="PhishingCampaignRecord",
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
                ("has_sent", models.BooleanField(default=False)),
                ("is_clicked", models.BooleanField(default=False)),
                ("is_opened", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="PhishingTemplate",
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
                ("name", models.CharField(max_length=256)),
                ("description", models.TextField(blank=True, null=True)),
                ("is_public", models.BooleanField(default=False)),
                ("email_body", models.TextField(blank=True, null=True)),
                (
                    "email_subject",
                    models.CharField(blank=True, max_length=256, null=True),
                ),
                (
                    "email_sender",
                    models.EmailField(blank=True, max_length=254, null=True),
                ),
                (
                    "email_sender_name",
                    models.CharField(blank=True, max_length=256, null=True),
                ),
                (
                    "email_domain",
                    models.CharField(blank=True, max_length=256, null=True),
                ),
                ("email_host", models.CharField(blank=True, max_length=256, null=True)),
                ("email_port", models.IntegerField(blank=True, null=True)),
                (
                    "email_username",
                    models.CharField(blank=True, max_length=256, null=True),
                ),
                (
                    "email_password",
                    models.CharField(blank=True, max_length=256, null=True),
                ),
                ("email_use_tls", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
    ]