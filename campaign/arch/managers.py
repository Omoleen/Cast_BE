import uuid

import pendulum
from django.db import models
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from abstract.managers import SimpleManager, SimpleModelManager
from campaign.enums import CampaignStatus
from content.models import CampaignContentSnapshot, Content
from content.serializers import ContentSerializer
from courses.models import Course, CourseCampaign, CourseContent, EmployeeCourseCampaign
from courses.serializers import (
    CourseCampaignSerializer,
    CourseContentSerializer,
    CourseListSerializer,
    CourseSerializer,
)
from phishing.enums import EmailDeliveryTypes
from phishing.models import PhishingCampaign, PhishingTemplate
from phishing.serializers import (
    PhishingCampaignDetailedSerializer,
    PhishingCampaignSerializer,
    PhishingTemplateSerializer,
)
from quiz.models import CampaignContentQuiz, Question
from quiz.serializers import CampaignContentQuizSerializer, QuestionSerializer
from users.enums import EmployeeStatuses
from users.models import Employee, EmployeeProfile, Organization
from users.serializers import EmployeeProfileSerializer, EmployeeSerializer

from ..enums import CampaignTypes
from ..models import Campaign
from ..serializers import (
    CampaignContentSnapshotSerializer,
    CampaignSerializer,
    ContentQuestionSerializer,
    EmployeeCampaignListSerializer,
)
from ..tasks import initiate_campaign_task


class CourseCampaignManagerStep1(SimpleModelManager):
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
            "automatically_enroll_employees",
            "last_step_completed",
        ]
        # depth = 1
        extra_kwargs = {
            "id": {"read_only": True},
            "last_step_completed": {"read_only": True},
            "status": {"read_only": True},
        }

    def _transform_data(self, attrs):
        attrs["last_step_completed"] = 1
        return super()._transform_data(attrs)

    def _validate_fields(self, attrs):
        attrs = super()._validate_fields(attrs)
        now = timezone.now()
        if attrs["type"] == CampaignTypes.PHISHING:
            raise serializers.ValidationError("Invalid campaign type")
        if attrs.get("start_date") and attrs.get("end_date"):
            if attrs["start_date"] > attrs["end_date"]:
                raise serializers.ValidationError("Invalid date range")
            if attrs["start_date"] < now:
                raise serializers.ValidationError("Invalid start date")
        return attrs

    def _validate_db(self, attrs):
        model = self.Meta.model
        if model.objects.filter(
            name=attrs.get("name"), organization=self.context["request"].user
        ).exists():
            raise serializers.ValidationError("Invalid campaign")
        attrs["organization"] = self.context["request"].user
        return attrs

    def _create(self, validated_data):
        campaign = self.Meta.model.objects.create(**validated_data)
        CourseCampaign.objects.create(campaign=campaign)
        return campaign


class CourseCampaignManagerUpdateStep1(SimpleModelManager):
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
            "automatically_enroll_employees",
            "last_step_completed",
        ]
        # depth = 1
        extra_kwargs = {
            "id": {"read_only": True},
            "last_step_completed": {"read_only": True},
            "status": {"read_only": True},
        }

    def _validate_fields(self, attrs):
        attrs = super()._validate_fields(attrs)
        now = timezone.now()
        if attrs.get("type") == CampaignTypes.PHISHING:
            raise serializers.ValidationError("Invalid campaign type")
        if attrs.get("start_date") and attrs.get("end_date"):
            if attrs["start_date"] > attrs["end_date"]:
                raise serializers.ValidationError("Invalid date range")
            if attrs["start_date"] < now:
                raise serializers.ValidationError("Invalid start date")
        return attrs

    def _validate_db(self, attrs):
        model = self.Meta.model
        if (
            model.objects.filter(
                name=attrs.get("name"), organization=self.context["request"].user
            )
            .exclude(id=self.instance.id)
            .exists()
        ):
            raise serializers.ValidationError("This campaign name already exists")
        return attrs

    def _update(self, instance, validated_data):
        campaign = instance
        campaign.name = validated_data.get("name", campaign.name)
        campaign.description = validated_data.get("description", campaign.description)
        campaign.start_date = validated_data.get("start_date", campaign.start_date)
        campaign.end_date = validated_data.get("end_date", campaign.end_date)
        campaign.automatically_enroll_employees = validated_data.get(
            "automatically_enroll_employees", campaign.automatically_enroll_employees
        )
        campaign.save()
        return campaign


class PhishingCampaignManagerStep1(SimpleModelManager):
    email_delivery_type = serializers.ChoiceField(
        write_only=True, required=True, choices=EmailDeliveryTypes.choices
    )
    email_delivery_date = serializers.DateTimeField(write_only=True, required=False)
    email_delivery_start_date = serializers.DateTimeField(
        write_only=True, required=False
    )
    email_delivery_end_date = serializers.DateTimeField(write_only=True, required=False)

    class Meta:
        model = Campaign
        fields = [
            "id",
            "name",
            "description",
            "type",
            "status",
            "email_delivery_type",
            "email_delivery_date",
            "email_delivery_start_date",
            "email_delivery_end_date",
            "automatically_enroll_employees",
            "last_step_completed",
        ]
        # depth = 1
        extra_kwargs = {
            "id": {"read_only": True},
            "last_step_completed": {"read_only": True},
            "status": {"read_only": True},
            "type": {"read_only": True},
        }

    def _transform_data(self, attrs):
        attrs["last_step_completed"] = 1
        return super()._transform_data(attrs)

    def _validate_fields(self, attrs):
        attrs = super()._validate_fields(attrs)
        now = timezone.now()
        match attrs["email_delivery_type"]:
            case EmailDeliveryTypes.IMMEDIATELY:
                attrs["email_delivery_date"] = None
                attrs["email_delivery_start_date"] = None
                attrs["email_delivery_end_date"] = None
            case EmailDeliveryTypes.SCHEDULED_RANGE:
                if now > attrs.get("email_delivery_start_date"):
                    raise serializers.ValidationError("Invalid start date")
                if not attrs.get("email_delivery_start_date") or not attrs.get(
                    "email_delivery_end_date"
                ):
                    raise serializers.ValidationError(
                        "Email delivery start and end date are required for scheduled delivery"
                    )
                if attrs.get("email_delivery_start_date") > attrs.get(
                    "email_delivery_end_date"
                ):
                    raise serializers.ValidationError("Invalid date range")
                attrs["email_delivery_date"] = None
            case EmailDeliveryTypes.SCHEDULED:
                if now > attrs.get("email_delivery_date"):
                    raise serializers.ValidationError("Invalid date")
                if not attrs.get("email_delivery_date"):
                    raise serializers.ValidationError(
                        "Email delivery date is required for scheduled delivery"
                    )
                attrs["email_delivery_start_date"] = None
                attrs["email_delivery_end_date"] = None
            case _:
                raise serializers.ValidationError("Invalid email delivery type")
        return attrs

    def _validate_db(self, attrs):
        model = self.Meta.model
        if model.objects.filter(
            name=attrs.get("name"), organization=self.context["request"].user
        ).exists():
            raise serializers.ValidationError("Invalid campaign")
        attrs["organization"] = self.context["request"].user
        return attrs

    def _create(self, validated_data):
        email_delivery_type = validated_data.pop("email_delivery_type")
        email_delivery_date = validated_data.pop("email_delivery_date", None)
        email_delivery_start_date = validated_data.pop(
            "email_delivery_start_date", None
        )
        email_delivery_end_date = validated_data.pop("email_delivery_end_date", None)
        campaign = self.Meta.model.objects.create(
            type=CampaignTypes.PHISHING, **validated_data
        )
        PhishingCampaign.objects.create(
            campaign=campaign,
            email_delivery_type=email_delivery_type,
            email_delivery_date=email_delivery_date,
            email_delivery_start_date=email_delivery_start_date,
            email_delivery_end_date=email_delivery_end_date,
        )
        return campaign


class PhishingCampaignManagerUpdateStep1(SimpleModelManager):
    email_delivery_type = serializers.ChoiceField(
        write_only=True, required=True, choices=EmailDeliveryTypes.choices
    )
    email_delivery_date = serializers.DateTimeField(
        write_only=True, required=False, allow_null=True
    )
    email_delivery_start_date = serializers.DateTimeField(
        write_only=True, required=False
    )
    email_delivery_end_date = serializers.DateTimeField(write_only=True, required=False)

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
            "email_delivery_type",
            "email_delivery_date",
            "email_delivery_start_date",
            "email_delivery_end_date",
            "automatically_enroll_employees",
            "last_step_completed",
        ]
        # depth = 1
        extra_kwargs = {
            "id": {"read_only": True},
            "last_step_completed": {"read_only": True},
            "status": {"read_only": True},
            "type": {"read_only": True},
            "start_date": {"read_only": True},
            "end_date": {"read_only": True},
        }

    def _validate_fields(self, attrs):
        attrs = super()._validate_fields(attrs)
        now = timezone.now()
        match attrs["email_delivery_type"]:
            case EmailDeliveryTypes.IMMEDIATELY:
                attrs["email_delivery_date"] = None
                attrs["email_delivery_start_date"] = None
                attrs["email_delivery_end_date"] = None
            case EmailDeliveryTypes.SCHEDULED_RANGE:
                if now > attrs.get("email_delivery_start_date"):
                    raise serializers.ValidationError("Invalid start date")
                if not attrs.get("email_delivery_start_date") or not attrs.get(
                    "email_delivery_end_date"
                ):
                    raise serializers.ValidationError(
                        "Email delivery start and end date are required for scheduled delivery"
                    )
                if attrs.get("email_delivery_start_date") > attrs.get(
                    "email_delivery_end_date"
                ):
                    raise serializers.ValidationError("Invalid date range")
                attrs["email_delivery_date"] = None
            case EmailDeliveryTypes.SCHEDULED:
                if now > attrs.get("email_delivery_date"):
                    raise serializers.ValidationError("Invalid date")
                if not attrs.get("email_delivery_date"):
                    raise serializers.ValidationError(
                        "Email delivery date is required for scheduled delivery"
                    )
                attrs["email_delivery_start_date"] = None
                attrs["email_delivery_end_date"] = None
            case _:
                raise serializers.ValidationError("Invalid email delivery type")
        return attrs

    def _validate_db(self, attrs):
        model = self.Meta.model
        if (
            model.objects.filter(
                name=attrs.get("name"), organization=self.context["request"].user
            )
            .exclude(id=self.instance.id)
            .exists()
        ):
            raise serializers.ValidationError("Invalid campaign")
        return attrs

    def _update(self, instance, validated_data):
        campaign: Campaign = instance
        campaign.name = validated_data.get("name", campaign.name)
        campaign.description = validated_data.get("description", campaign.description)
        campaign.automatically_enroll_employees = validated_data.get(
            "automatically_enroll_employees", campaign.automatically_enroll_employees
        )
        campaign.save()
        phishing_campaign: PhishingCampaign = campaign.phishing_campaign
        email_delivery_type = validated_data.pop("email_delivery_type")
        email_delivery_date = validated_data.pop("email_delivery_date", None)
        email_delivery_start_date = validated_data.pop(
            "email_delivery_start_date", None
        )
        email_delivery_end_date = validated_data.pop("email_delivery_end_date", None)
        phishing_campaign.email_delivery_type = email_delivery_type
        phishing_campaign.email_delivery_date = email_delivery_date
        phishing_campaign.email_delivery_start_date = email_delivery_start_date
        phishing_campaign.email_delivery_end_date = email_delivery_end_date
        phishing_campaign.save()
        phishing_campaign.update_campaign_dates()
        return campaign


class CampaignManagerStep2(SimpleModelManager):
    employees_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True
    )
    employees = EmployeeSerializer(many=True, read_only=True)

    class Meta:
        model = Campaign
        fields = ["employees", "employees_ids"]

    def _transform_data(self, attrs):
        attrs["last_step_completed"] = 2
        return super()._transform_data(attrs)

    def _validate_db(self, attrs):
        campaign: Campaign = self.instance
        if campaign.last_step_completed < 1:
            raise serializers.ValidationError("Complete the first step")
        return attrs

    def _update(self, instance, validated_data):
        employees_ids: uuid.UUID = validated_data.pop("employees_ids")

        campaign: Campaign = instance

        employees_objs = (
            Employee.objects.select_related("emp_profile")
            .filter(
                id__in=employees_ids,
                emp_profile__organization=self.context["request"].user,
            )
            .exclude(emp_profile__status=EmployeeStatuses.DEACTIVATED)
        )

        campaign.set_employees(employees_objs)

        campaign.last_step_completed = max(
            validated_data["last_step_completed"], campaign.last_step_completed
        )
        campaign.save()

        return campaign

    def _to_representation(self, instance):
        return "Employees added successfully"


class CourseCampaignManagerStep3(SimpleModelManager):
    course_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True)
    courses = CourseListSerializer(many=True, read_only=True)

    class Meta:
        model = Campaign
        fields = ["course_ids", "courses"]

    def _transform_data(self, attrs):
        attrs["last_step_completed"] = 3
        return super()._transform_data(attrs)

    def _validate_fields(self, attrs):

        if not attrs.get("course_ids"):
            raise serializers.ValidationError("course_ids is required")
        return super()._validate_fields(attrs)

    def _validate_db(self, attrs):
        campaign: Campaign = self.instance
        if campaign.last_step_completed < 2:
            raise serializers.ValidationError("Complete the second step")
        if campaign.type == CampaignTypes.PHISHING:
            raise serializers.ValidationError(
                "This endpoint cannot be called for a phishing campaign"
            )
        courses = Course.objects.filter(id__in=attrs["course_ids"]).filter(
            Q(organization=self.context["request"].user) | Q(is_public=True)
        )
        if not courses.exists():
            raise serializers.ValidationError("Invalid Course")
        if courses.count() != len(attrs["course_ids"]):
            raise serializers.ValidationError("Invalid Course")
        self.courses = courses
        return super()._validate_db(attrs)

    def _update(self, instance, validated_data):
        campaign: Campaign = instance
        organization: Organization = self.context["request"].user
        courses = self.courses
        course_campaign, _ = CourseCampaign.objects.update_or_create(
            campaign=campaign,
        )
        course_campaign.courses.set(courses)
        # deprecated

        campaign.last_step_completed = max(
            validated_data["last_step_completed"], campaign.last_step_completed
        )

        campaign.save()
        return campaign

    def _to_representation(self, instance):
        return CourseListSerializer(self.courses, many=True).data


class PhishingCampaignManagerStep3(SimpleModelManager):
    phishing_template_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True
    )
    # phishing = PhishingCampaignSerializer(read_only=True)

    class Meta:
        model = Campaign
        fields = [
            "phishing_template_ids",
            # "phishing"
        ]

    def _transform_data(self, attrs):
        attrs["last_step_completed"] = 3
        return super()._transform_data(attrs)

    def _validate_fields(self, attrs):
        campaign: Campaign = self.instance
        organization: Organization = self.context["request"].user
        if campaign.last_step_completed < 2:
            raise serializers.ValidationError("Complete the second step")
        if campaign.type != CampaignTypes.PHISHING:
            raise serializers.ValidationError(
                "This endpoint is only for a phishing campaign"
            )
        templates: models.QuerySet = PhishingTemplate.objects.filter(
            Q(organization=organization) | Q(is_public=True),
            id__in=attrs["phishing_template_ids"],
        )
        if not templates.exists():
            raise serializers.ValidationError("Invalid Phishing Template")
        self.templates = templates
        return super()._validate_fields(attrs)

    def _update(self, instance, validated_data):
        templates = self.templates
        campaign: Campaign = instance
        phishing_campaign: PhishingCampaign = campaign.phishing_campaign

        if not phishing_campaign:
            raise serializers.ValidationError("Phishing campaign not found")

        phishing_campaign.phishing_templates.set(templates)

        campaign.last_step_completed = max(
            validated_data["last_step_completed"], campaign.last_step_completed
        )
        campaign.save()
        return campaign

    def _to_representation(self, instance):
        return "Phishing campaign updated successfully"


class CampaignManagerStep4(SimpleModelManager):
    class Meta:
        model = Campaign
        fields = []

    def _validate_db(self, attrs):
        campaign: Campaign = self.instance
        if campaign.last_step_completed < 3:
            raise serializers.ValidationError("Complete the third step")
        return super()._validate_db(attrs)

    def _update(self, instance, validated_data):
        campaign: Campaign = instance
        campaign.last_step_completed = 4
        campaign.status = CampaignStatus.SCHEDULED
        campaign.save()
        return campaign

    def _misc(self, data):
        campaign: Campaign = self.obj
        initiate_campaign_task.delay(campaign.id)
        return

    def _to_representation(self, instance):
        return "Campaign created successfully"


class LearningCampaignCourseListMetricsSerializer(serializers.ModelSerializer):
    average_score = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "average_score",
            "completion_rate",
        ]

    def get_average_score(self, obj: Course):
        all_course_campaign_courses = CourseCampaign.objects.filter(
            courses__id=obj.id, campaign=self.context["campaign"]
        )
        total_score = 0
        for course_campaign in all_course_campaign_courses:
            total_score += course_campaign.average_score
        return (
            total_score / all_course_campaign_courses.count()
            if all_course_campaign_courses
            else 0
        )

    def get_completion_rate(self, obj: Course):
        all_course_campaign_courses = CourseCampaign.objects.filter(
            courses__id=obj.id, campaign=self.context["campaign"]
        )
        total_completion_rate = 0
        for course_campaign in all_course_campaign_courses:
            total_completion_rate += course_campaign.progress_rate
        return (
            total_completion_rate / all_course_campaign_courses.count()
            if all_course_campaign_courses
            else 0
        )


class CourseCampaignEmployeeMetricsSerializer(serializers.ModelSerializer):
    department = serializers.CharField(source="department.name")
    progress_rate = serializers.SerializerMethodField()
    status = serializers.CharField(source="emp_profile.status")
    average_score = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            "id",
            "email",
            "department",
            "first_name",
            "last_name",
            "progress_rate",
            "average_score",
            "status",
        ]

    def get_progress_rate(self, obj: Employee):
        campaign: Campaign = self.context["campaign"]
        employee_course_campaign = EmployeeCourseCampaign.objects.filter(
            employee=obj, course_campaign__campaign=campaign
        ).first()
        return employee_course_campaign.progress_rate if employee_course_campaign else 0

    def get_average_score(self, obj: Employee):
        campaign: Campaign = self.context["campaign"]
        employee_course_campaign = EmployeeCourseCampaign.objects.filter(
            employee=obj, course_campaign__campaign=campaign
        ).first()

        return (
            employee_course_campaign.average_score if employee_course_campaign else None
        )


class CourseCampaignMetricsSerializer(serializers.ModelSerializer):
    courses = LearningCampaignCourseListMetricsSerializer(read_only=True, many=True)
    employees = CourseCampaignEmployeeMetricsSerializer(many=True, read_only=True)

    class Meta:
        model = CourseCampaign
        fields = ["courses", "employees"]


class CourseCampaignMetricsManager(SimpleModelManager):
    completion_rate = serializers.SerializerMethodField()
    average_score = serializers.SerializerMethodField()
    cut_off_score = serializers.FloatField(
        read_only=True, source="organization.org_profile.cut_off_score"
    )
    course_campaign = CourseCampaignMetricsSerializer(
        read_only=True,
    )

    class Meta:
        model = Campaign
        fields = [
            "id",
            "name",
            "status",
            "course_campaign",
            "completion_rate",
            "average_score",
            "cut_off_score",
        ]

    def get_completion_rate(self, obj: Campaign):
        campaign: Campaign = obj
        course_campaign: CourseCampaign = campaign.course_campaign
        return course_campaign.progress_rate if course_campaign else 0

    def get_average_score(self, obj: Campaign):
        campaign: Campaign = obj
        course_campaign: CourseCampaign = campaign.course_campaign
        return course_campaign.average_score if course_campaign else None


class PhishingCampaignMetricsManager(SimpleModelManager):
    phishing_campaign = PhishingCampaignSerializer(read_only=True)

    class Meta:
        model = Campaign
        fields = [
            "id",
            "status",
            "phishing_campaign",
        ]


class PhishingCampaignDetailedMetricsManager(SimpleModelManager):
    phishing_campaign = PhishingCampaignDetailedSerializer(read_only=True)

    class Meta:
        model = Campaign
        fields = [
            "id",
            "status",
            "phishing_campaign",
        ]


class CancelCampaignManager(SimpleModelManager):
    class Meta:
        model = Campaign
        fields = []

    def _update(self, instance, validated_data):
        campaign: Campaign = instance
        campaign.cancel()
        return campaign


class StartCourseCampaignManager(SimpleModelManager):
    class Meta:
        model = Campaign
        fields = []

    def _validate_db(self, attrs):
        campaign: Campaign = self.instance
        course_campaign: CourseCampaign = campaign.course_campaign
        employee: Employee = self.context["request"].user
        now = timezone.now()

        if campaign.start_date > now:
            raise serializers.ValidationError("Campaign has not started yet")
        if campaign.end_date < now:
            raise serializers.ValidationError("Campaign has ended")

        employee_record = course_campaign.employee_records.filter(
            employee=employee
        ).first()
        if not employee_record:
            raise serializers.ValidationError("Employee record not found")
        if employee_record.is_started:
            raise serializers.ValidationError("Campaign already started")
        self.employee_record = employee_record
        return super()._validate_db(attrs)

    def _update(self, instance, validated_data):
        employee_record = self.employee_record
        employee_record.start()
        return instance

    def _to_representation(self, instance):
        return "Campaign started successfully"
