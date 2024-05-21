import pendulum
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from abstract.views import (
    SimpleCreateGenericView,
    SimpleDeleteOneGenericView,
    SimpleGetDetailGenericView,
    SimpleGetListGenericView,
    SimplePartialUpdateGenericView,
)
from campaign.enums import CampaignStatus, CampaignTypes
from Castellum.enums import Roles
from Castellum.permissions import IsEmployee, IsOrganization
from phishing.models import EmployeePhishingCampaign, PhishingTemplate
from phishing.serializers import PhishingCampaignEmployeeRecordSerializer

from .arch.managers import (
    CampaignManagerStep2,
    CampaignManagerStep4,
    CancelCampaignManager,
    CourseCampaignManagerStep1,
    CourseCampaignManagerStep3,
    CourseCampaignManagerUpdateStep1,
    CourseCampaignMetricsManager,
    PhishingCampaignDetailedMetricsManager,
    PhishingCampaignManagerStep1,
    PhishingCampaignManagerStep3,
    PhishingCampaignManagerUpdateStep1,
    PhishingCampaignMetricsManager,
    StartCourseCampaignManager,
)
from .enums import CampaignStatus, CampaignTypes
from .models import Campaign
from .serializers import (
    CampaignSerializer,
    EmployeeCampaignListSerializer,
    EmployeeDetailedCourseCampaignSerializer,
    OrganizationCampaignEmployeePreviewListSerializer,
    OrganizationCampaignListSerializer,
)


@extend_schema_view(
    post=extend_schema(
        summary="Create Course Campaign - Step 1",
        description="Create a new course campaign. - Step 1",
    ),
)
class CourseCampaignCreateViewStep1(SimpleCreateGenericView):
    serializer_class = CourseCampaignManagerStep1
    permission_classes = [IsOrganization]


@extend_schema_view(
    patch=extend_schema(
        summary="Update Course Campaign - Step 1",
        description="Update an existing course campaign. - Step 1",
    ),
)
class CourseCampaignUpdateViewStep1(SimplePartialUpdateGenericView):
    serializer_class = CourseCampaignManagerUpdateStep1
    permission_classes = [IsOrganization]
    queryset = Campaign.objects.all()

    def get_queryset(self):
        return self.queryset.filter(organization=self.request.user).exclude(
            status__in=[
                CampaignStatus.ACTIVE,
                CampaignStatus.COMPLETED,
                CampaignStatus.CANCELLED,
            ]
        )


@extend_schema_view(
    post=extend_schema(
        summary="Create Phishing Campaign - Step 1",
        description="Create a new phishing campaign. - Step 1",
    ),
)
class PhishingCampaignCreateViewStep1(SimpleCreateGenericView):
    serializer_class = PhishingCampaignManagerStep1
    permission_classes = [IsOrganization]


@extend_schema_view(
    patch=extend_schema(
        summary="Update Phishing Campaign - Step 1",
        description="Update an existing phishing campaign. - Step 1",
    ),
)
class PhishingCampaignUpdateViewStep1(SimplePartialUpdateGenericView):
    serializer_class = PhishingCampaignManagerUpdateStep1
    permission_classes = [IsOrganization]
    queryset = Campaign.objects.all()

    def get_queryset(self):
        return self.queryset.filter(organization=self.request.user).exclude(
            status__in=[
                CampaignStatus.ACTIVE,
                CampaignStatus.COMPLETED,
                CampaignStatus.CANCELLED,
            ]
        )


@extend_schema_view(
    patch=extend_schema(
        summary="Update Campaign - Step 2",
        description="Update an existing campaign. - Step 2",
    ),
)
class CampaignCreateViewStep2(SimplePartialUpdateGenericView):
    serializer_class = CampaignManagerStep2
    permission_classes = [IsOrganization]
    queryset = Campaign.objects.all()

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(organization=self.request.user)
            .exclude(
                status__in=[
                    CampaignStatus.ACTIVE,
                    CampaignStatus.COMPLETED,
                    CampaignStatus.CANCELLED,
                ]
            )
        )


@extend_schema_view(
    patch=extend_schema(
        summary="Update Course Campaign - Step 3",
        description="Update an existing course campaign. - Step 3",
    ),
)
class CourseCampaignCreateViewStep3(SimplePartialUpdateGenericView):
    serializer_class = CourseCampaignManagerStep3
    permission_classes = [IsOrganization]
    queryset = Campaign.objects.prefetch_related("phishing_campaign").all()

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(organization=self.request.user)
            .exclude(
                status__in=[
                    CampaignStatus.ACTIVE,
                    CampaignStatus.COMPLETED,
                    CampaignStatus.CANCELLED,
                ]
            )
        )


@extend_schema_view(
    patch=extend_schema(
        summary="Update Phishing Campaign - Step 3",
        description="Update an existing phishing campaign. - Step 3",
    ),
)
class PhishingCampaignCreateViewStep3(SimplePartialUpdateGenericView):
    serializer_class = PhishingCampaignManagerStep3
    permission_classes = [IsOrganization]
    queryset = Campaign.objects.all()

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(organization=self.request.user)
            .exclude(
                status__in=[
                    CampaignStatus.ACTIVE,
                    CampaignStatus.COMPLETED,
                    CampaignStatus.CANCELLED,
                ]
            )
        )


@extend_schema_view(
    patch=extend_schema(
        summary="Submit Campaign - Step 4",
        description="Submit an existing campaign. - Step 4",
    ),
)
class CampaignCreateViewStep4(SimplePartialUpdateGenericView):
    serializer_class = CampaignManagerStep4
    permission_classes = [IsOrganization]
    queryset = Campaign.objects.prefetch_related(
        "phishing_campaign",
        "course_campaign",
        "phishing_campaign__campaign",
        "course_campaign__campaign",
    ).all()

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(organization=self.request.user)
            .exclude(
                status__in=[
                    CampaignStatus.ACTIVE,
                    CampaignStatus.CANCELLED,
                    CampaignStatus.COMPLETED,
                ]
            )
        )


@extend_schema_view(
    get=extend_schema(
        summary="Get Campaigns",
        description="Get all campaigns for the logged in Organization.",
        parameters=[
            OpenApiParameter(
                name="type",
                type=str,
                description="Type of campaign to filter by.",
                required=False,
            ),
            OpenApiParameter(
                name="status",
                type=str,
                description="Status of campaign to filter by.",
                required=False,
            ),
            OpenApiParameter(
                name="search",
                type=str,
                description="Search query to filter by.",
                required=False,
            ),
        ],
    )
)
class OrganizationCampaignListView(generics.ListAPIView):
    serializer_class = OrganizationCampaignListSerializer
    permission_classes = [IsOrganization]
    queryset = Campaign.objects.all()

    def filter_queryset(self, queryset):
        type = self.request.query_params.get("type", None)
        status = self.request.query_params.get("status", None)
        search_query = self.request.query_params.get("search", None)
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        if type:
            queryset = queryset.filter(type=type)
        if status:
            queryset = queryset.filter(status=status)
        return super().filter_queryset(queryset)

    def get_queryset(self):
        return self.request.user.org_campaigns.all()


@extend_schema_view(
    get=extend_schema(
        summary="Get Campaign Detail",
        description="Get the details of a campaign for the logged in Organization.",
    ),
    delete=extend_schema(
        summary="Delete Campaign",
        description="Delete a campaign for the logged in Organization.",
    ),
)
class OrganizationCampaignDetailView(
    generics.RetrieveDestroyAPIView,
):
    serializer_class = CampaignSerializer
    permission_classes = [IsOrganization]
    queryset = Campaign.objects.all()
    lookup_field = "id"

    def get_queryset(self):
        return self.request.user.org_campaigns.all()


@extend_schema_view(
    get=extend_schema(
        summary="Get Employees in a Campaign",
        description="Get the list of employees in a campaign.",
    ),
)
class OrganizationCampaignEmployeePreviewListView(
    generics.ListAPIView,
):
    serializer_class = OrganizationCampaignEmployeePreviewListSerializer
    permission_classes = [IsOrganization]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        campaign_id = self.kwargs.get("id")
        campaign: Campaign = Campaign.objects.filter(id=campaign_id).first()
        if not campaign:
            return EmployeePhishingCampaign.objects.none()
        if campaign.is_course_campaign:
            return campaign.course_campaign.employees.all()
        return campaign.phishing_campaign.employees.all()


@extend_schema_view(
    get=extend_schema(
        summary="Get Course Campaigns Metrics",
        description="Get the metrics of course campaigns for the logged in Organization.",
    ),
)
class CourseCampaignMetricsView(
    SimpleGetDetailGenericView,
):
    serializer_class = CourseCampaignMetricsManager
    permission_classes = [IsOrganization]
    queryset = Campaign.objects.all()

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                organization__id=self.request.user.id,
                status__in=[CampaignStatus.ACTIVE, CampaignStatus.COMPLETED],
            )
            .exclude(type=CampaignTypes.PHISHING)
        )

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        return Response(
            self.serializer_class(
                obj, context=dict(request=request, campaign=obj)
            ).data,
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    get=extend_schema(
        summary="Get Phishing Campaign Metrics",
        description="Get the metrics of phishing campaigns for the logged in Organization.",
    ),
)
class PhishingCampaignMetricsView(SimpleGetDetailGenericView):
    serializer_class = PhishingCampaignMetricsManager
    permission_classes = [IsOrganization]
    queryset = Campaign.objects.all()

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                organization__id=self.request.user.id,
                type=CampaignTypes.PHISHING,
                status__in=[CampaignStatus.ACTIVE, CampaignStatus.COMPLETED],
            )
        )

    # def get(self, request, *args, **kwargs):
    #     obj = self.get_object()
    #     return Response(
    #         self.serializer_class(
    #             obj, context=dict(request=request, campaign=obj, **self.kwargs)
    #         ).data,
    #         status=status.HTTP_200_OK,
    #     )


@extend_schema_view(
    get=extend_schema(
        summary="Get Phishing Campaign Metrics - Phishing Template",
        description="Get the metrics of phishing campaigns(phishing template) for the logged in Organization.",
    )
)
class PhishingCampaignDetailedMetricsView(SimpleGetDetailGenericView):
    serializer_class = PhishingCampaignDetailedMetricsManager
    permission_classes = [IsOrganization]
    queryset = Campaign.objects.all()

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                organization__id=self.request.user.id,
                type=CampaignTypes.PHISHING,
                status__in=[CampaignStatus.ACTIVE, CampaignStatus.COMPLETED],
            )
        )


# class PhishingCampaignEmployeeRecordView(SimpleGetListGenericView):
#     serializer_class = PhishingCampaignEmployeeRecordSerializer
#     permission_classes = [IsOrganization]
#     queryset = EmployeePhishingCampaign.objects.all()
#     pagination_class = PageNumberPagination


@extend_schema_view(
    patch=extend_schema(
        summary="Cancel Campaign",
        description="Cancel a campaign.",
    )
)
class CancelCampaignView(SimplePartialUpdateGenericView):
    serializer_class = CancelCampaignManager
    permission_classes = [IsOrganization]
    queryset = Campaign.objects.all()

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                organization=self.request.user,
                status__in=[CampaignStatus.ACTIVE, CampaignStatus.SCHEDULED],
            )
        )

    def _to_representation(self, instance):
        return "Campaign has been cancelled successfully."
