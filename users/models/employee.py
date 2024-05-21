from datetime import timedelta

import pendulum
from django.conf import settings
from django.db import models
from django.utils import timezone

from abstract.models import BaseModel
from abstract.tasks import send_email
from Castellum.enums import Roles
from users.enums import ActivityType

from ..enums import EmployeeStatuses
from ..managers import EmployeeManager
from ..typed_dicts import LearningResourcesData
from .user import User, UserTimeSeriesCompletedCourses, UserTimeSeriesSecurityScore


class EmployeeProfile(BaseModel):
    employee = models.OneToOneField(
        "Employee", on_delete=models.CASCADE, related_name="emp_profile"
    )
    staff_id = models.CharField(max_length=256, null=True, blank=True)
    first_name = models.CharField(max_length=256, null=True, blank=True)
    last_name = models.CharField(max_length=256, null=True, blank=True)
    department = models.ForeignKey(
        "Department", models.SET_NULL, null=True, related_name="employee_profiles"
    )
    organization = models.ForeignKey(
        "Organization", on_delete=models.CASCADE, related_name="employee_profiles"
    )
    security_score = models.FloatField(blank=True, null=True)
    status = models.CharField(
        max_length=50,
        choices=EmployeeStatuses.choices,
        default=EmployeeStatuses.PENDING,
    )
    deactivated_at = models.DateTimeField(null=True, blank=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Employee(User):
    objects = EmployeeManager()

    base_role = Roles.EMPLOYEE

    class Meta:
        proxy = True

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if not self.id or self.pk is None:
            self.role = self.base_role
        return super().save(*args, **kwargs)

    def create_employee_profile(self, *args, **kwargs):
        return EmployeeProfile.objects.create(employee=self, *args, **kwargs)

    def deactivate_account(self):
        self.is_active = False
        self.emp_profile.status = EmployeeStatuses.DEACTIVATED
        self.emp_profile.deactivated_at = timezone.now()
        self.emp_profile.save()
        self.save()

    def activate_account(self):
        self.is_active = True
        self.emp_profile.status = EmployeeStatuses.ACTIVE
        self.emp_profile.deactivated_at = None
        self.emp_profile.save()
        self.save()

    def perform_activity(self, activity_type: ActivityType):
        from .organization import ActivityLog

        activity_log = ActivityLog(
            employee=self,
            organization=self.emp_profile.organization,
            type=activity_type,
        )
        activity_log.save()

    @property
    def employees_leaderboard(self):
        return self.emp_profile.organization.employees_leaderboard

    @property
    def ongoing_employee_campaign(self):
        from campaign.enums import CampaignStatus
        from campaign.models import Campaign
        from courses.models import EmployeeCourseCampaign

        return EmployeeCourseCampaign.objects.filter(
            employee=self,
            course_campaign__campaign__status=CampaignStatus.ACTIVE,
            is_started=True,
            is_completed=False,
        ).first()

    @property
    def progress_rate(self):
        from courses.models import EmployeeCourseCampaign

        course_campaigns = EmployeeCourseCampaign.objects.filter(
            employee=self, is_started=True
        )
        progress_rates = [
            course_campaign.progress_rate for course_campaign in course_campaigns
        ]
        return int(sum(progress_rates) / len(progress_rates)) if progress_rates else 0

    @property
    def learning_resources(self) -> LearningResourcesData:
        from Castellum.enums import LearningTypes
        from courses.models import Course
        from employees.serializers import LearningResourceCourseSerializer

        from ..enums import CourseCardType, LearningResourceButtonType

        now = timezone.now()
        user = self
        new_courses = (
            Course.objects.filter(created_at__gte=now - timedelta(days=30))
            .exclude(
                users_attempted__user=user,
            )
            .filter(
                models.Q(organization=user.emp_profile.organization)
                | models.Q(is_public=True)
            )
        )
        recommended_courses = (
            Course.objects.exclude(users_attempted__user=user)
            .filter(
                models.Q(organization=user.emp_profile.organization)
                | models.Q(is_public=True)
            )
            .order_by("?")
        )
        ongoing_courses = Course.objects.filter(
            users_attempted__user=user,
            users_attempted__is_completed=False,
            users_attempted__is_started=True,
        ).filter(
            models.Q(organization=user.emp_profile.organization)
            | models.Q(is_public=True)
        )
        completed_courses = Course.objects.filter(
            users_attempted__user=user, users_attempted__is_completed=True
        ).filter(
            models.Q(organization=user.emp_profile.organization)
            | models.Q(is_public=True)
        )

        data = {
            "all": {
                "new": LearningResourceCourseSerializer(
                    new_courses[:2],
                    context=dict(
                        button_text=LearningResourceButtonType.BEGIN,
                        course_card_type=CourseCardType.NEW,
                    ),
                    many=True,
                ).data,
                "ongoing": LearningResourceCourseSerializer(
                    ongoing_courses[:2],
                    context=dict(
                        button_text=LearningResourceButtonType.CONTINUE,
                        course_card_type=CourseCardType.IN_PROGRESS,
                    ),
                    many=True,
                ).data,
                "completed": LearningResourceCourseSerializer(
                    completed_courses[:2],
                    context=dict(
                        button_text=LearningResourceButtonType.RETAKE,
                        course_card_type=CourseCardType.COMPLETED,
                    ),
                    many=True,
                ).data,
                "recommended": LearningResourceCourseSerializer(
                    recommended_courses[:2],
                    context=dict(
                        button_text=LearningResourceButtonType.BEGIN,
                        course_card_type=CourseCardType.NEW,
                    ),
                    many=True,
                ).data,
            },
            "general": {
                "new": LearningResourceCourseSerializer(
                    new_courses.filter(learning_type=LearningTypes.GENERAL)[:2],
                    context=dict(
                        button_text=LearningResourceButtonType.BEGIN,
                        course_card_type=CourseCardType.NEW,
                    ),
                    many=True,
                ).data,
                "ongoing": LearningResourceCourseSerializer(
                    ongoing_courses.filter(learning_type=LearningTypes.GENERAL)[:2],
                    context=dict(
                        button_text=LearningResourceButtonType.CONTINUE,
                        course_card_type=CourseCardType.IN_PROGRESS,
                    ),
                    many=True,
                ).data,
                "completed": LearningResourceCourseSerializer(
                    completed_courses.filter(learning_type=LearningTypes.GENERAL)[:2],
                    context=dict(
                        button_text=LearningResourceButtonType.RETAKE,
                        course_card_type=CourseCardType.COMPLETED,
                    ),
                    many=True,
                ).data,
                "recommended": LearningResourceCourseSerializer(
                    recommended_courses.filter(learning_type=LearningTypes.GENERAL)[:2],
                    context=dict(
                        button_text=LearningResourceButtonType.BEGIN,
                        course_card_type=CourseCardType.NEW,
                    ),
                    many=True,
                ).data,
            },
            "specialized": {
                "new": LearningResourceCourseSerializer(
                    new_courses.filter(learning_type=LearningTypes.SPECIALIZED)[:2],
                    context=dict(
                        button_text=LearningResourceButtonType.BEGIN,
                        course_card_type=CourseCardType.NEW,
                    ),
                    many=True,
                ).data,
                "ongoing": LearningResourceCourseSerializer(
                    ongoing_courses.filter(learning_type=LearningTypes.SPECIALIZED)[:2],
                    context=dict(
                        button_text=LearningResourceButtonType.CONTINUE,
                        course_card_type=CourseCardType.IN_PROGRESS,
                    ),
                    many=True,
                ).data,
                "completed": LearningResourceCourseSerializer(
                    completed_courses.filter(learning_type=LearningTypes.SPECIALIZED)[
                        :2
                    ],
                    context=dict(
                        button_text=LearningResourceButtonType.RETAKE,
                        course_card_type=CourseCardType.COMPLETED,
                    ),
                    many=True,
                ).data,
                "recommended": LearningResourceCourseSerializer(
                    recommended_courses.filter(learning_type=LearningTypes.SPECIALIZED)[
                        :2
                    ],
                    context=dict(
                        button_text=LearningResourceButtonType.BEGIN,
                        course_card_type=CourseCardType.NEW,
                    ),
                    many=True,
                ).data,
            },
        }
        return data

    @property
    def active_campaigns(self):
        from campaign.enums import CampaignStatus
        from campaign.models import Campaign

        return Campaign.objects.filter(
            models.Q(
                course_campaign__employee_records__is_started=True,
                course_campaign__employee_records__is_completed=False,
            )
            | models.Q(status=CampaignStatus.ACTIVE),
            organization=self.emp_profile.organization,
            course_campaign__employee_records__employee=self,
        )

    @property
    def active_campaigns_count(self):
        return self.active_campaigns.count()

    @property
    def completed_campaigns(self):
        from campaign.enums import CampaignStatus
        from campaign.models import Campaign

        return Campaign.objects.filter(
            models.Q(
                course_campaign__employee_records__is_started=True,
                course_campaign__employee_records__is_completed=True,
            )
            | models.Q(status=CampaignStatus.COMPLETED),
            course_campaign__employee_records__employee=self,
            organization=self.emp_profile.organization,
        )

    @property
    def completed_campaigns_count(self) -> int:
        return self.completed_campaigns.count()

    @property
    def phishing_reported_count(self):
        from phishing.models import EmployeePhishingCampaign

        return EmployeePhishingCampaign.objects.filter(
            employee=self, is_reported=True
        ).count()

    @property
    def course_campaigns_queryset(self) -> models.QuerySet["Campaign"]:
        from campaign.models import Campaign
        from courses.models import CourseCampaign

        return Campaign.objects.filter(course_campaign__in=self.course_campaign.all())

    @property
    def phishing_campaigns_queryset(self) -> models.QuerySet["Campaign"]:
        from campaign.models import Campaign
        from courses.models import CourseCampaign

        return Campaign.objects.filter(
            phishing_campaign__in=self.phishing_campaigns.all()
        )

    @property
    def first_name(self):
        return self.emp_profile.first_name

    @property
    def last_name(self):
        return self.emp_profile.last_name

    @property
    def full_name(self):
        return self.emp_profile.full_name

    @property
    def department(self):
        return self.emp_profile.department

    @property
    def security_score_timeseries_last_30_days(self):
        last_30_days = timezone.now() - timedelta(days=30)
        return UserTimeSeriesSecurityScore.objects.filter(
            created_at__gte=last_30_days, user=self
        ).order_by("created_at")

    @property
    def courses_completed_timeseries_last_30_days(self):
        last_30_days = timezone.now() - timedelta(days=30)
        return UserTimeSeriesCompletedCourses.objects.filter(
            created_at__gte=last_30_days, user=self
        ).order_by("created_at")

    @property
    def security_score_timeseries_last_7days(self):
        last_7_days = timezone.now() - timedelta(days=7)
        return UserTimeSeriesSecurityScore.objects.filter(
            created_at__gte=last_7_days, user=self
        ).order_by("created_at")

    @property
    def courses_completed_timeseries_last_7days(self):
        last_7_days = timezone.now() - timedelta(days=7)
        return UserTimeSeriesCompletedCourses.objects.filter(
            created_at__gte=last_7_days, user=self
        ).order_by("created_at")
