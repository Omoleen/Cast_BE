from abstract.managers import SimpleModelManager

from ..models import EmployeePhishingCampaign, PhishingTemplate


class PhishingCampaignClickedManager(SimpleModelManager):
    class Meta:
        model = EmployeePhishingCampaign
        fields = []

    def update(self, instance: EmployeePhishingCampaign, validated_data):
        instance.click_link()
        return instance


class PhishingCampaignOpenedManager(SimpleModelManager):
    class Meta:
        model = EmployeePhishingCampaign
        fields = []

    def update(self, instance: EmployeePhishingCampaign, validated_data):
        instance.open_email()
        return instance


class PhishingCampaignCompromisedManager(SimpleModelManager):
    class Meta:
        model = EmployeePhishingCampaign
        fields = []

    def update(self, instance: EmployeePhishingCampaign, validated_data):
        instance.compromise()
        return instance


class DetailedPhishingTemplateManager(SimpleModelManager):
    class Meta:
        model = PhishingTemplate
        fields = [
            "id",
            "organization",
            "name",
            "description",
            "vendor",
            "email_html_content",
            "email_css_styles",
            "email_subject",
            "landing_page_html_content",
            "landing_page_css_styles",
        ]
