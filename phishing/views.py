from django.db.models import Q
from django.http import HttpResponse
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.permissions import AllowAny

from abstract.views import (
    SimpleGetDetailGenericView,
    SimpleGetListGenericView,
    SimpleUpdateGenericView,
)
from Castellum.permissions import IsOrganization
from phishing.serializers import PhishingTemplateSerializer

from .arch.managers import (
    DetailedPhishingTemplateManager,
    PhishingCampaignClickedManager,
    PhishingCampaignCompromisedManager,
    PhishingCampaignOpenedManager,
)
from .models import EmployeePhishingCampaign, PhishingTemplate


@extend_schema_view(
    get=extend_schema(
        summary="Phishing Template List",
        description="Get a list of all phishing templates",
    ),
)
class PhishingTemplateListView(generics.ListAPIView):
    queryset = PhishingTemplate.objects.all()
    permission_classes = [IsOrganization]
    serializer_class = PhishingTemplateSerializer

    def get_queryset(self):
        return self.queryset.filter(
            Q(organization=self.request.user) | Q(is_public=True)
        )


@extend_schema_view(
    get=extend_schema(
        summary="Phishing Template Detail",
        description="Get the details of a phishing template",
    ),
)
class DetailedPhishingTemplateView(SimpleGetDetailGenericView):
    queryset = PhishingTemplate.objects.all()
    permission_classes = [IsOrganization]
    serializer_class = DetailedPhishingTemplateManager
    lookup_field = "id"


@extend_schema_view(
    patch=extend_schema(
        summary="Phishing Campaign Clicked",
        description="Mark a phishing campaign as clicked",
    ),
)
class PhishingCampaignClickedView(SimpleUpdateGenericView):
    queryset = EmployeePhishingCampaign.objects.all()
    permission_classes = [AllowAny]
    serializer_class = PhishingCampaignClickedManager
    lookup_field = "id"


@extend_schema_view(
    patch=extend_schema(
        summary="Phishing Campaign Opened",
        description="Mark a phishing campaign as opened",
    ),
)
class PhishingCampaignOpenedView(SimpleUpdateGenericView):
    queryset = EmployeePhishingCampaign.objects.all()
    permission_classes = [AllowAny]
    serializer_class = PhishingCampaignOpenedManager
    lookup_field = "id"

    # def get(self, request, *args, **kwargs):
    #     instance: EmployeePhishingCampaign = self.get_object()
    #     instance.open_email()
    # print("Opened email.......")
    # pixel = b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
    # return HttpResponse(pixel, content_type="image/gif")


@extend_schema_view(
    patch=extend_schema(
        summary="Phishing Campaign Compromised",
        description="Mark a phishing campaign as compromised",
    ),
)
class PhishingCampaignCompromisedView(SimpleUpdateGenericView):
    queryset = EmployeePhishingCampaign.objects.all()
    permission_classes = [AllowAny]
    serializer_class = PhishingCampaignCompromisedManager
    lookup_field = "id"
