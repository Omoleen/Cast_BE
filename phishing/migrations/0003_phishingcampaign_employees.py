# Generated by Django 4.1.7 on 2024-04-10 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_answeredquestion_user_course_and_more"),
        ("phishing", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="phishingcampaign",
            name="employees",
            field=models.ManyToManyField(
                blank=True, related_name="phishing_campaigns", to="users.employee"
            ),
        ),
    ]