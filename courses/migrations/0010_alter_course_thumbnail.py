# Generated by Django 4.1.7 on 2024-05-16 12:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0009_coursecampaign_reminder_task_ids"),
    ]

    operations = [
        migrations.AlterField(
            model_name="course",
            name="thumbnail",
            field=models.FileField(
                blank=True, null=True, upload_to="course_thumbnails/"
            ),
        ),
    ]