from rest_framework import serializers

from campaign.enums import CampaignStatus
from users.models import Employee


class EmployeeLeaderboardSerializer(serializers.ModelSerializer):
    department = serializers.CharField(source="department.name")

    class Meta:
        model = Employee
        fields = ["full_name", "department"]


class EmployeeCourseCampaignCountSerializer(serializers.ModelSerializer):
    upcoming_campaigns_count = serializers.SerializerMethodField()
    in_progress_campaigns_count = serializers.IntegerField(
        source="active_campaigns_count"
    )

    class Meta:
        model = Employee
        fields = [
            "upcoming_campaigns_count",
            "in_progress_campaigns_count",
            "completed_campaigns_count",
        ]

    def get_upcoming_campaigns_count(self, employee: Employee) -> int:
        return employee.course_campaigns_queryset.filter(
            status=CampaignStatus.SCHEDULED
        ).count()

    def get_in_progress_campaigns_count(self, employee: Employee) -> int:
        return employee.course_campaigns_queryset.filter(
            status=CampaignStatus.ACTIVE
        ).count()
