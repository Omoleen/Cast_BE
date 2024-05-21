from django.db import models


class CampaignTypes(models.TextChoices):
    SPECIALIZED = "specialized", "Specialized"
    GENERAL = "general", "General"
    PHISHING = "phishing", "Phishing"


class CampaignStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    DRAFT = "draft", "Draft"
    SCHEDULED = "scheduled", "Scheduled"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
