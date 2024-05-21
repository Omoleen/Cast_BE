from django.db import models
from django.db.models import Q
from rest_framework import serializers

from abstract.managers import SimpleManager, SimpleModelManager
from campaign.enums import CampaignStatus
from content.models import CampaignContentSnapshot, Content
from content.serializers import ContentSerializer
from courses.models import Course, CourseCampaign, CourseContent
from courses.models.course_campaign import EmployeeCourseCampaign
from courses.serializers import (
    CourseCampaignSerializer,
    CourseContentSerializer,
    CourseSerializer,
    EmployeeCourseCampaignSerializer,
)
from phishing.enums import EmailDeliveryTypes
from phishing.models import PhishingCampaign, PhishingTemplate
from phishing.serializers import PhishingCampaignSerializer, PhishingTemplateSerializer
from quiz.models import CampaignContentQuiz, Question
from quiz.serializers import CampaignContentQuizSerializer, QuestionSerializer
from users.enums import EmployeeStatuses
from users.models import Employee, EmployeeProfile, Organization
from users.serializers import EmployeeProfileSerializer, EmployeeSerializer

from .enums import CampaignTypes
from .models import Campaign


class CampaignContentSnapshotSerializer(serializers.ModelSerializer):
    content_questions = CampaignContentQuizSerializer(many=True, read_only=True)
    content = ContentSerializer(read_only=True)

    class Meta:
        model = CampaignContentSnapshot
        fields = ["id", "content", "content_questions"]


class CampaignSerializer(serializers.ModelSerializer):
    phishing_campaign = PhishingCampaignSerializer(read_only=True)
    course_campaign = CourseCampaignSerializer(read_only=True)

    class Meta:
        model = Campaign
        fields = [
            "id",
            "name",
            "description",
            "type",
            "status",
            "start_date",
            "end_date",
            "activity",
            "automatically_enroll_employees",
            "last_step_completed",
            "phishing_campaign",
            "course_campaign",
        ]


class OrganizationCampaignListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = [
            "id",
            "name",
            "type",
            "status",
            "start_date",
            "end_date",
            "activity",
            "automatically_enroll_employees",
            "last_step_completed",
            "is_phishing_campaign",
            "is_course_campaign",
        ]


class OrganizationCampaignEmployeePreviewListSerializer(serializers.ModelSerializer):
    department = serializers.CharField(source="emp_profile.department.name")

    class Meta:
        model = Employee
        fields = ["id", "full_name", "department"]


class EmployeeCampaignListSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = ["id", "name", "progress", "expiry", "start_date", "type", "status"]

    def get_progress(self, obj) -> int:
        employee: Employee = self.context["request"].user
        return (
            EmployeeCourseCampaign.objects.filter(
                employee=employee, course_campaign__campaign=obj
            )
            .first()
            .progress_rate
        )


class EmployeeDetailedCourseCampaignSerializer(serializers.ModelSerializer):
    course_campaign = EmployeeCourseCampaignSerializer(read_only=True)
    employee_has_started_campaign = serializers.SerializerMethodField()
    employee_has_completed_campaign = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            "id",
            "name",
            "description",
            "type",
            "start_date",
            "course_campaign",
            "employee_has_started_campaign",
            "employee_has_completed_campaign",
        ]

    def get_employee_has_started_campaign(self, campaign: Campaign) -> bool:
        employee: Employee = self.context["request"].user
        return (
            EmployeeCourseCampaign.objects.filter(
                employee=employee, course_campaign__campaign=campaign
            )
            .first()
            .is_started
        )

    def get_employee_has_completed_campaign(self, campaign: Campaign) -> bool:
        employee: Employee = self.context["request"].user
        return (
            EmployeeCourseCampaign.objects.filter(
                employee=employee, course_campaign__campaign=campaign
            )
            .first()
            .is_completed
        )


class ContentQuestionSerializer(serializers.Serializer):
    question_ids = serializers.ListField(
        child=serializers.UUIDField(write_only=True), write_only=True
    )
    content_id = serializers.UUIDField(write_only=True)
    # question = serializers.CharField(read_only=True)
    # answer = serializers.CharField()
