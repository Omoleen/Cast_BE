from django.db import models


class EmailDeliveryTypes(models.TextChoices):
    IMMEDIATELY = "immediately", "Immediately"
    SCHEDULED = "scheduled", "Scheduled"
    SCHEDULED_RANGE = "scheduled_range", "Scheduled Range"


class PhishingActions(models.TextChoices):
    CLICKED = "clicked", "Clicked"
    OPENED = "opened", "Opened"
    COMPROMISED = "compromised", "Compromised"
    REPORTED = "reported", "Reported"
    NO_ACTION = "no_action", "No Action"
