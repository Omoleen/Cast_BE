from django.urls import path

from .views import (
    EmployeeCampaignListView,
    EmployeeCompleteRegistrationView,
    EmployeeCourseCampaignCountView,
    EmployeeDashboardView,
    EmployeeDetailedCourseCampaignView,
    EmployeeLearningResourcesView,
    EmployeeProfileView,
    EmployeesAnswerCourseCampaignQuestionView,
    EmployeesCompleteCourseCampaignContentView,
    EmployeesCompleteCourseCampaignView,
    EmployeeStartCourseCampaignView,
)

urlpatterns = [
    path("profile/", EmployeeProfileView.as_view(), name="employee-profile"),
    path("dashboard/", EmployeeDashboardView.as_view(), name="employee-dashboard"),
    path(
        "dashboard/learning-resources/",
        EmployeeLearningResourcesView.as_view(),
        name="employee-learning-resources",
    ),
    path(
        "campaigns/", EmployeeCampaignListView.as_view(), name="employee-campaign-list"
    ),
    path(
        "campaigns/count/",
        EmployeeCourseCampaignCountView.as_view(),
        name="employee-campaign-count",
    ),
    path(
        "campaigns/<uuid:campaign_id>/",
        EmployeeDetailedCourseCampaignView.as_view(),
        name="employee-detailed-campaign",
    ),
    path(
        "campaigns/<uuid:campaign_id>/start/",
        EmployeeStartCourseCampaignView.as_view(),
        name="employee-start-campaign",
    ),
    path(
        "campaigns/<uuid:campaign_id>/courses/<uuid:course_id>/contents/<uuid:content_id>/questions/<uuid:question_id>/answer/",
        EmployeesAnswerCourseCampaignQuestionView.as_view(),
        name="employee-answer-campaign-question",
    ),
    path(
        "campaigns/<uuid:campaign_id>/courses/<uuid:course_id>/contents/<uuid:content_id>/complete/",
        EmployeesCompleteCourseCampaignContentView.as_view(),
        name="employee-complete-course-campaign-content",
    ),
    path(
        "campaigns/<uuid:campaign_id>/complete/",
        EmployeesCompleteCourseCampaignView.as_view(),
        name="employee-complete-course-campaign",
    ),
    path(
        "<str:token>/complete-registration/",
        EmployeeCompleteRegistrationView.as_view(),
        name="employee-complete-registration",
    ),
]
