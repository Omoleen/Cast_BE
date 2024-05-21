import uuid
from datetime import timedelta

import pendulum
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone

from abstract.models import BaseModel
from abstract.tasks import send_email, update_model_field
from campaign.enums import CampaignStatus, CampaignTypes
from Castellum.celery import app
from Castellum.enums import Roles
from users.enums import ActivityType, EmployeeStatuses

from ..managers import OrganizationManager
from .employee import Employee
from .user import User


class OrganizationProfile(BaseModel):
    organization = models.OneToOneField(
        "Organization", on_delete=models.CASCADE, related_name="org_profile"
    )
    name = models.CharField(max_length=256, null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    cut_off_score = models.FloatField(default=0)
    security_score = models.FloatField(null=True, blank=True)

    campaign_email_notification = models.BooleanField(
        "Employees receive an email with every new campaign they are enrolled in",
        default=True,
    )
    campaign_completion_notification = models.BooleanField(
        "Employees receive an email every time they complete a campaign", default=True
    )
    reminder_notification = models.BooleanField(
        "Employees receive an email and reminders, instructing them to complete the campaign before the deadline.",
        default=True,
    )

    phishing_report_email = models.EmailField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.name}'s Profile"


class Organization(User):
    objects = OrganizationManager()

    base_role = Roles.ORGANIZATION

    class Meta:
        proxy = True

    def __str__(self) -> str:
        return self.org_profile.name

    def save(self, *args, **kwargs):
        if not self.id or self.pk is None:
            self.role = self.base_role
        return super().save(*args, **kwargs)

    @property
    def security_score(self):
        self.org_profile.security_score

    @property
    def employees_leaderboard(self):
        return Employee.objects.filter(emp_profile__organization=self).order_by(
            "-emp_profile__security_score"
        )[:10]

    @property
    def campaign_stats(self):
        campaigns = self.org_campaigns
        return {
            "phishing_campaigns": campaigns.filter(
                type=CampaignTypes.PHISHING,
                start_date__gte=timezone.now() - timedelta(days=14),
                start_date__lte=timezone.now(),
            ).count(),
            "learning_campaigns": campaigns.exclude(type=CampaignTypes.PHISHING)
            .filter(
                start_date__gte=timezone.now() - timedelta(days=14),
                start_date__lte=timezone.now(),
            )
            .count(),
            "active_learning_campaigns": campaigns.filter(
                status=CampaignStatus.ACTIVE,
            )
            .exclude(type=CampaignTypes.PHISHING)
            .count(),
        }

    @property
    def organization_training_completion_rate(self):
        from courses.models import CourseCampaign

        progress_rates = [
            course_campaign.progress_rate
            for course_campaign in CourseCampaign.objects.filter(
                campaign__organization=self
            ).values()
        ]
        if progress_rates:
            return sum(progress_rates) / len(progress_rates)
        return 0

    @property
    def employees_security_stats(self):
        from users.models import Department, Employee

        employees = Employee.objects.prefetch_related("emp_profile").filter(
            emp_profile__organization=self
        )
        risk_rating = {
            "high": employees.filter(emp_profile__security_score__lt=40).count(),
            "medium": employees.filter(
                emp_profile__security_score__gt=40, emp_profile__security_score__lt=70
            ).count(),
            "low": employees.filter(
                emp_profile__security_score__gte=70,
            ).count(),
        }

        return {
            "employees_count": employees.count(),
            "active_employees_count": employees.filter(
                emp_profile__status=EmployeeStatuses.ACTIVE
            ).count(),
            "inactive_employees_count": employees.exclude(
                emp_profile__status=EmployeeStatuses.ACTIVE
            ).count(),
            "departments_count": self.departments.all().count(),
            "risk_rating": risk_rating,
        }

    @property
    def departments_security_stats(self):
        from users.models import Department

        departments = Department.objects.filter(organization=self)
        graph_data = []
        for department in departments:
            department_employees = Employee.objects.prefetch_related(
                "emp_profile"
            ).filter(emp_profile__department=department)
            temp_data = {
                "name": department.name,
                "security_score": department.security_score,
                "employees_data": {
                    "count": department_employees.count(),
                    "high_risk": department_employees.filter(
                        emp_profile__security_score__gte=settings.HIGH_RISK_SCORE_RANGE[
                            0
                        ],
                        emp_profile__security_score__lte=settings.HIGH_RISK_SCORE_RANGE[
                            1
                        ],
                    ).count(),
                    "medium_risk": department_employees.filter(
                        emp_profile__security_score__gte=settings.MEDIUM_RISK_SCORE_RANGE[
                            0
                        ],
                        emp_profile__security_score__lte=settings.MEDIUM_RISK_SCORE_RANGE[
                            1
                        ],
                    ).count(),
                    "low_risk": department_employees.filter(
                        emp_profile__security_score__gte=settings.LOW_RISK_SCORE_RANGE[
                            0
                        ],
                        emp_profile__security_score__lte=settings.LOW_RISK_SCORE_RANGE[
                            1
                        ],
                    ).count(),
                },
            }
            graph_data.append(temp_data)
        return graph_data

    @property
    def courses_phishing_campaign_stats(self):
        last_30_days = timezone.now() - timedelta(days=30)
        last_30_days_range = pendulum.period(last_30_days, timezone.now())

        last_30_days_data = []
        count = 0
        for dt in last_30_days_range.range("weeks"):
            count += 1
            temp_data = {
                "name": f"Week {count}",
                "learning_campaigns": self.org_campaigns.exclude(
                    type=CampaignTypes.PHISHING
                )
                .filter(
                    start_date__gte=dt.start_of("week"),
                    start_date__lte=dt.end_of("week"),
                )
                .count(),
                "phishing_campaigns": self.org_campaigns.filter(
                    type=CampaignTypes.PHISHING,
                    start_date__gte=dt.start_of("week"),
                    start_date__lte=dt.end_of("week"),
                ).count(),
            }
            last_30_days_data.append(temp_data)

        this_week_start = pendulum.now().start_of("week")
        this_week_end = pendulum.now().end_of("week")
        this_week_data = {
            "name": "This Week",
            "learning_campaigns": self.org_campaigns.exclude(
                type=CampaignTypes.PHISHING
            )
            .filter(
                start_date__gte=this_week_start,
                start_date__lte=this_week_end,
            )
            .count(),
            "phishing_campaigns": self.org_campaigns.filter(
                type=CampaignTypes.PHISHING,
                start_date__gte=this_week_start,
                start_date__lte=this_week_end,
            ).count(),
        }

        last_30_days_data.append(this_week_data)

        now = timezone.now()

        start_date = now - timedelta(days=7)

        last_7_days_data = []

        for i in range(7):
            day = start_date + timedelta(days=i)
            next_day = day + timedelta(days=1)

            temp_data = {
                "name": day.strftime("%A"),  # Get the day name (e.g., Monday)
                "learning_campaigns": self.org_campaigns.exclude(
                    type=CampaignTypes.PHISHING
                )
                .filter(Q(start_date__gte=day) & Q(start_date__lt=next_day))
                .count(),
                "phishing_campaigns": self.org_campaigns.filter(
                    type=CampaignTypes.PHISHING,
                    start_date__gte=day,
                    start_date__lt=next_day,
                ).count(),
            }
            last_7_days_data.append(temp_data)

        last_7_days_data[-1]["name"] = "Today"
        data = {"last_30_days": last_30_days_data, "last_7_days": last_7_days_data}

        return data


class AuthorizedDomain(BaseModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="authorized_domains"
    )
    email = models.EmailField(null=True)
    domain = models.CharField(max_length=256)
    verified_on = models.DateTimeField(null=True)
    verification_token = models.CharField(max_length=256, null=True, blank=True)
    verification_background_task_id = models.CharField(
        max_length=256, null=True, blank=True
    )

    def verify_domain(self):
        self.verified_on = timezone.now()
        self.verification_token = None
        self.save()
        return False

    def send_domain_verification_email(self):
        self.set_token()
        context = {
            "verification_url": f"{settings.FRONTEND_URL}domain-verification/{self.verification_token}"
        }
        email_subject = "Verify your domain"
        # email_body = f"Click on the link to verify your domain: {settings.FRONTEND_URL}{self.verification_token}"
        email_body = render_to_string(
            "emails/users/domain_verification.html", context=context
        )
        email = self.email
        send_email.delay(
            email_subject=email_subject, email_body=email_body, to_email=email
        )
        return

    def set_token(
        self,
    ):
        if self.verification_background_task_id:
            app.control.revoke(self.verification_background_task_id)
        self.verification_token = str(uuid.uuid4().hex)
        verification_background_task = update_model_field.apply_async(
            args=["AuthorizedDomain", self.id, "verification_token", uuid.uuid4().hex],
            countdown=timedelta(minutes=15).seconds,
        )
        self.verification_background_task_id = str(verification_background_task.id)
        self.save()
        return


class DeliverabilityTest(BaseModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="deliverability_tests"
    )
    email = models.EmailField(null=True)
    verified_on = models.DateTimeField(null=True)
    verification_token = models.CharField(max_length=256, null=True, blank=True)
    verification_background_task_id = models.CharField(
        max_length=256, null=True, blank=True
    )

    def verify_domain(self):
        self.verified_on = timezone.now()
        self.verification_token = None
        self.save()
        return False

    def send_domain_verification_email(self):
        self.set_token()
        context = {
            "verification_url": f"{settings.FRONTEND_URL}deliverability-test/{self.verification_token}"
        }
        email_subject = "Confirm the email was delivered to you"
        # email_body = f"Click on this link to confirm you received this email: {settings.FRONTEND_URL}{self.verification_token}"
        email_body = render_to_string(
            "emails/users/deliverability_test.html", context=context
        )
        email = self.email
        send_email.delay(
            email_subject=email_subject, email_body=email_body, to_email=email
        )
        return

    def set_token(
        self,
    ):
        if self.verification_background_task_id:
            app.control.revoke(self.verification_background_task_id)
        self.verification_token = str(uuid.uuid4().hex)
        verification_background_task = update_model_field.apply_async(
            args=[
                "DeliverabilityTest",
                self.id,
                "verification_token",
                uuid.uuid4().hex,
            ],
            countdown=timedelta(minutes=15).seconds,
        )
        self.verification_background_task_id = str(verification_background_task.id)
        self.save()
        return


class ActivityLog(BaseModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="org_activity_logs"
    )
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="emp_activity_logs"
    )
    type = models.CharField(
        max_length=256,
        choices=ActivityType.choices,
        default=ActivityType.COURSE_CAMPAIGN_STARTED,
    )

    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.type} - {self.employee.email}"
