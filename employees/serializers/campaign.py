from rest_framework import serializers

from campaign.models import Campaign
from courses.models import EmployeeCourseCampaign


class OngoingEmployeeCampaignSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="course_campaign.campaign.name")
    type = serializers.CharField(source="course_campaign.campaign.type")
    end_date = serializers.CharField(source="course_campaign.campaign.end_date")
    id = serializers.CharField(source="course_campaign.campaign.id")

    class Meta:
        model = EmployeeCourseCampaign
        fields = ["name", "type", "end_date", "progress_rate", "id"]
