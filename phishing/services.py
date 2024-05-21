from functools import cached_property

from campaign.models import Campaign

from .models import PhishingCampaign


class PhishingManager:
    def __init__(self, campaign: Campaign, *args, **kwargs):
        self.campaign: Campaign = campaign
        self.phishing_campaign: PhishingCampaign = campaign.phishing_campaign
        self.employees = []

        self.get_employees()

    def get_employees(self):
        self.employees = self.campaign.employees.all()
        return self.employees

    def handle(self):
        self.phishing_campaign.initiate_phishing_campaign()
        return self.phishing_campaign


class PhishingTemplateManager:
    def __init__(self, *args, **kwargs):
        ...

    def handle(self):
        ...

    def preview(self):
        ...

    @cached_property
    def html_template(self):
        ...


class PhishingCampaignManager:
    def __init__(self) -> None:
        ...

    def handle(self):
        ...
