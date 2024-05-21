# Generated by Django 4.1.7 on 2024-05-06 14:29

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0012_rename_sent_to_authorizeddomain_email_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeliverabilityTest",
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
                ("email", models.EmailField(max_length=254, null=True)),
                ("verified_on", models.DateTimeField(null=True)),
                (
                    "verification_token",
                    models.CharField(blank=True, max_length=256, null=True),
                ),
                (
                    "verification_background_task_id",
                    models.CharField(blank=True, max_length=256, null=True),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="deliverability_tests",
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
