import pendulum
from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from abstract.views import (
    SimpleCreateGenericView,
    SimpleDeleteOneGenericView,
    SimpleGetDetailGenericView,
    SimpleGetListGenericView,
    SimplePartialUpdateGenericView,
    SimpleUpdateGenericView,
)
from campaign.arch.managers import (
    CampaignManagerStep2,
    CampaignManagerStep4,
    CancelCampaignManager,
    CourseCampaignManagerStep1,
    CourseCampaignManagerStep3,
    CourseCampaignManagerUpdateStep1,
    CourseCampaignMetricsManager,
    PhishingCampaignManagerStep1,
    PhishingCampaignManagerStep3,
    PhishingCampaignMetricsManager,
    StartCourseCampaignManager,
)
from campaign.enums import CampaignStatus, CampaignTypes
from campaign.models import Campaign
from campaign.serializers import (
    CampaignSerializer,
    EmployeeCampaignListSerializer,
    EmployeeDetailedCourseCampaignSerializer,
    OrganizationCampaignListSerializer,
)
from Castellum.enums import Roles
from Castellum.permissions import IsEmployee, IsOrganization
from content.models import Content
from employees.arch.managers import (
    EmployeeCompleteRegistrationManager,
    EmployeeDashboardManager,
    EmployeeLearningResourceManager,
    EmployeesAnswerCourseCampaignQuestionManager,
    EmployeesCompleteCourseCampaignContentManager,
    EmployeesCompleteCourseCampaignManager,
)
from quiz.models import Question
from users.models import Employee
from users.serializers import EmployeeSerializer

from .serializers import EmployeeCourseCampaignCountSerializer


@extend_schema_view(
    get=extend_schema(
        summary="Employee Profile",
        description="Get the profile of the authenticated employee",
    ),
)
class EmployeeProfileView(SimpleGetDetailGenericView):
    serializer_class = EmployeeSerializer
    permission_classes = [IsEmployee]
    queryset = Employee.objects.all()

    def get_object(self):
        return self.request.user


@extend_schema_view(
    get=extend_schema(
        summary="Employee Complete Registration",
        description="Get employee details to complete registration",
    ),
    patch=extend_schema(
        summary="Employee Complete Registration",
        description="Complete employee registration",
    ),
)
class EmployeeCompleteRegistrationView(
    SimpleUpdateGenericView, SimpleGetDetailGenericView
):
    permission_classes = [AllowAny]
    lookup_field = "token"
    lookup_url_kwarg = "token"
    serializer_class = EmployeeCompleteRegistrationManager
    queryset = Employee.objects.all()


@extend_schema_view(
    get=extend_schema(
        summary="Employee Campaign List",
        description="Get the list of campaigns for the authenticated employee",
        parameters=[
            OpenApiParameter(
                name="status",
                type=str,
                required=False,
                description="Filter campaigns by status",
                enum=["active", "scheduled", "completed"],
            )
        ],
    ),
)
class EmployeeCampaignListView(generics.ListAPIView):
    serializer_class = EmployeeCampaignListSerializer
    permission_classes = [IsEmployee]
    queryset = Campaign.objects.all()

    def filter_queryset(self, queryset):
        from django.db import models

        status = self.request.query_params.get("status")
        match status:
            case CampaignStatus.ACTIVE:
                return self.request.user.active_campaigns
            case CampaignStatus.SCHEDULED:
                return queryset.filter(status=CampaignStatus.SCHEDULED)
            case CampaignStatus.COMPLETED:
                return self.request.user.completed_campaigns
            case _:
                return queryset

    def get_queryset(self):
        return self.request.user.course_campaigns_queryset.filter()


@extend_schema_view(
    get=extend_schema(
        summary="Employee Campaign Detail",
        description="Get the details of a campaign for the authenticated employee",
    ),
)
class EmployeeDetailedCourseCampaignView(SimpleGetDetailGenericView):
    serializer_class = EmployeeDetailedCourseCampaignSerializer
    permission_classes = [IsEmployee]
    queryset = Campaign.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "campaign_id"

    def get_queryset(self):
        return self.request.user.course_campaigns_queryset.filter(
            status=CampaignStatus.ACTIVE
        )


@extend_schema_view(
    get=extend_schema(
        summary="Get Count of Employee Campaigns",
        description="Get the count of campaigns based on statuses for the authenticated employee",
    )
)
class EmployeeCourseCampaignCountView(SimpleGetDetailGenericView):
    serializer_class = EmployeeCourseCampaignCountSerializer
    permission_classes = [IsEmployee]
    queryset = Employee.objects.all()

    def get_object(self):
        return self.request.user


@extend_schema_view(
    patch=extend_schema(
        summary="Employee Start Course Campaign",
        description="Start a course campaign for the authenticated employee",
    ),
)
class EmployeeStartCourseCampaignView(SimplePartialUpdateGenericView):
    serializer_class = StartCourseCampaignManager
    permission_classes = [IsEmployee]
    queryset = Campaign.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "campaign_id"

    def get_queryset(self):
        return self.request.user.course_campaigns_queryset.filter(
            status=CampaignStatus.ACTIVE
        )


# class EmployeeCompleteCourseCampaignView(SimplePartialUpdateGenericView):
#     # serializer_class = CompleteCourseCamapignManager
#     permission_classes = [IsEmployee]
#     queryset = Campaign.objects.all()

#     def get_queryset(self):
#         return self.request.user.course_campaigns_queryset.filter(
#             status=CampaignStatus.ACTIVE
#         )


@extend_schema_view(
    patch=extend_schema(
        summary="Employee answer campaign question",
        description="Answer a campaign question for the authenticated employee",
    )
)
class EmployeesAnswerCourseCampaignQuestionView(SimpleUpdateGenericView):
    serializer_class = EmployeesAnswerCourseCampaignQuestionManager
    permission_classes = [IsEmployee]
    queryset = Question.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "question_id"

    def get_queryset(self):
        campaigns = self.request.user.course_campaigns_queryset.filter(
            status=CampaignStatus.ACTIVE
        )
        campaign = campaigns.filter(id=self.kwargs.get("campaign_id")).first()
        if not campaign:
            raise Http404

        course_campaign = campaign.course_campaign
        if not course_campaign.employees.filter(id=self.request.user.id).exists():
            raise Http404
        course = course_campaign.courses.filter(id=self.kwargs.get("course_id")).first()
        if not course:
            raise Http404
        content = course.contents.filter(id=self.kwargs.get("content_id")).first()
        if not content:
            raise Http404
        self.kwargs["content"] = content
        self.kwargs["course"] = course
        self.kwargs["course_campaign"] = course_campaign
        self.kwargs["campaign"] = campaign
        return content.questions.all()


@extend_schema_view(
    patch=extend_schema(
        summary="Employee Complete Course Campaign Content",
        description="Complete a course campaign content for the authenticated employee",
    )
)
class EmployeesCompleteCourseCampaignContentView(SimpleUpdateGenericView):
    serializer_class = EmployeesCompleteCourseCampaignContentManager
    permission_classes = [IsEmployee]
    queryset = Content.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "content_id"

    def get_queryset(self):
        campaigns = self.request.user.course_campaigns_queryset.filter(
            status=CampaignStatus.ACTIVE
        )
        campaign = campaigns.filter(id=self.kwargs.get("campaign_id")).first()
        if not campaign:
            raise Http404

        course_campaign = campaign.course_campaign
        if not course_campaign.employees.filter(id=self.request.user.id).exists():
            raise Http404
        course = course_campaign.courses.filter(id=self.kwargs.get("course_id")).first()
        if not course:
            raise Http404
        self.kwargs["course"] = course
        self.kwargs["course_campaign"] = course_campaign
        self.kwargs["campaign"] = campaign
        return course.contents.all()


@extend_schema_view(
    patch=extend_schema(
        summary="Employee complete a course in a campaign",
        description="Complete a course in a campaign for the authenticated employee",
    )
)
class EmployeesCompleteCourseCampaignView(SimpleUpdateGenericView):
    serializer_class = EmployeesCompleteCourseCampaignManager
    permission_classes = [IsEmployee]
    queryset = Campaign.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "campaign_id"

    def get_queryset(self):
        return self.request.user.course_campaigns_queryset.filter(
            status=CampaignStatus.ACTIVE
        )


@extend_schema_view(
    get=extend_schema(
        summary="Employee Dashboard",
        description="Get the dashboard of the authenticated employee",
    )
)
class EmployeeDashboardView(SimpleGetDetailGenericView):
    serializer_class = EmployeeDashboardManager
    permission_classes = [IsEmployee]
    queryset = Employee.objects.all()

    def get_object(self):
        return self.request.user


@extend_schema_view(
    get=extend_schema(
        summary="Employee Learning Resources",
        description="Get the learning resources of the authenticated employee",
    )
)
class EmployeeLearningResourcesView(SimpleGetDetailGenericView):
    serializer_class = EmployeeLearningResourceManager
    permission_classes = [IsEmployee]
    queryset = Employee.objects.all()

    def get_object(self):
        return self.request.user
