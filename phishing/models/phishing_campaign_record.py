from django.db import models

from abstract.models import BaseModel
from campaign.models import Campaign
from users.models import Employee

from . import PhishingCampaign
from .phishing_template import PhishingTemplate


class PhishingCampaignRecord(BaseModel):
    employee = models.OneToOneField(
        Employee, on_delete=models.CASCADE, related_name="phishing_records"
    )
    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="phishing_records"
    )
    phishing_campaign = models.ForeignKey(
        PhishingCampaign, on_delete=models.CASCADE, related_name="records"
    )
    # metrics
    has_sent = models.BooleanField(default=False)
    is_clicked = models.BooleanField(default=False)
    is_opened = models.BooleanField(default=False)
