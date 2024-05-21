from django.urls import path

from .views import *

app_name = "campaign"

urlpatterns = [
    path(
        "create/course/",
        CourseCampaignCreateViewStep1.as_view(),
        name="create-step-1",
    ),
    path(
        "create/phishing/",
        PhishingCampaignCreateViewStep1.as_view(),
        name="create-step-1",
    ),
    path(
        "course-campaigns/<str:id>/edit/1/",
        CourseCampaignUpdateViewStep1.as_view(),
        name="update-step-1-course",
    ),
    path(
        "phishing-campaigns/<str:id>/edit/1/",
        PhishingCampaignUpdateViewStep1.as_view(),
        name="update-step-1-phishing",
    ),
    path("<str:id>/edit/2/", CampaignCreateViewStep2.as_view(), name="create-step-2"),
    path(
        "course-campaigns/<str:id>/edit/3/",
        CourseCampaignCreateViewStep3.as_view(),
        name="update-step-3-course",
    ),
    path(
        "phishing-campaigns/<str:id>/edit/3/",
        PhishingCampaignCreateViewStep3.as_view(),
        name="update-step-3-phishing",
    ),
    path("<str:id>/submit/", CampaignCreateViewStep4.as_view(), name="submit"),
    path("", OrganizationCampaignListView.as_view(), name="campaign-list"),
    path(
        "<str:id>/",
        OrganizationCampaignDetailView.as_view(),
        name="get-delete-campaign",
    ),
    path(
        "<str:id>/preview/employees/",
        OrganizationCampaignEmployeePreviewListView.as_view(),
        name="preview-employees",
    ),
    path("<str:id>/cancel/", CancelCampaignView.as_view(), name="cancel-campaign"),
    path(
        "<str:id>/learning-metrics/",
        CourseCampaignMetricsView.as_view(),
        name="learning-metrics",
    ),
    path(
        "<str:id>/phishing-metrics/",
        PhishingCampaignMetricsView.as_view(),
        name="phishing-metrics",
    ),
    path(
        "<str:id>/phishing-metrics/<str:phishing_template_id>/",
        PhishingCampaignDetailedMetricsView.as_view(),
        name="phishing-metrics-phishing-template",
    ),
]
