from django.urls import path

from phishing.views import (
    DetailedPhishingTemplateView,
    PhishingCampaignClickedView,
    PhishingCampaignCompromisedView,
    PhishingCampaignOpenedView,
    PhishingTemplateListView,
)

urlpatterns = [
    path("templates/", PhishingTemplateListView.as_view(), name="phishing-list"),
    path(
        "templates/<uuid:id>/",
        DetailedPhishingTemplateView.as_view(),
        name="phishing-detail",
    ),
    path(
        "campaigns/<uuid:id>/clicked/",
        PhishingCampaignClickedView.as_view(),
        name="phishing-clicked",
    ),
    path(
        "campaigns/<uuid:id>/opened/",
        PhishingCampaignOpenedView.as_view(),
        name="phishing-email-opened",
    ),
    path(
        "campaigns/<uuid:id>/compromised/",
        PhishingCampaignCompromisedView.as_view(),
        name="phishing-compromised",
    ),
]
