from django.contrib import admin

from .models import (
    EmployeePhishingCampaign,
    PhishingCampaign,
    PhishingCampaignRecord,
    PhishingTemplate,
)

admin.site.register(PhishingCampaignRecord)


@admin.register(EmployeePhishingCampaign)
class EmployeePhishingCampaignAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "employee",
        "phishing_template",
        "is_opened",
        "is_clicked",
        "is_compromised",
        "is_reported",
    ]


@admin.register(PhishingTemplate)
class PhishingTemplateAdmin(admin.ModelAdmin):
    model = PhishingTemplate
    list_display = ["name", "vendor", "organization", "is_public"]
    list_filter = ["vendor", "organization", "is_public"]
    search_fields = ["name", "vendor", "organization"]


@admin.register(PhishingCampaign)
class PhishingCampaignAdmin(admin.ModelAdmin):
    model = PhishingCampaign
    list_display = [
        "campaign",
        "email_delivery_type",
        "email_delivery_date",
        "email_delivery_start_date",
        "email_delivery_end_date",
    ]
    list_filter = [
        "email_delivery_type",
        "email_delivery_date",
        "email_delivery_start_date",
        "email_delivery_end_date",
    ]
    fieldsets = [
        [
            None,
            {
                "fields": [
                    "campaign",
                    "email_delivery_type",
                    "email_delivery_date",
                    "email_delivery_start_date",
                    "email_delivery_end_date",
                ]
            },
        ]
    ]
