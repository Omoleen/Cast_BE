# Generated by Django 4.1.7 on 2024-05-16 12:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0008_alter_content_size"),
    ]

    operations = [
        migrations.AddField(
            model_name="content",
            name="thumbnail",
            field=models.FileField(
                blank=True, null=True, upload_to="thumbnails/courses/"
            ),
        ),
    ]
