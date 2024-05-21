from django.db import models

from abstract.models import BaseModel
from campaign.models import Campaign


class CampaignContentSnapshot(BaseModel):
    campaign = models.ForeignKey(
        Campaign, related_name="campaign_content_snapshots", on_delete=models.CASCADE
    )
    # all the fields in the content model
    content = models.JSONField()
