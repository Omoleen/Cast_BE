import collections
import random
from datetime import timedelta
from functools import cache

from django.db import models
from django.db.models import Q
from django.utils import timezone

from abstract.models import BaseModel
from campaign.enums import CampaignStatus
from campaign.models import Campaign
from campaign.tasks import start_campaign
from campaign.typed_dicts import CampaignActivity
from Castellum.celery import app
from phishing.toolboxes import PhishingSecurityScoreToolbox
from users.models import Department, Employee
from users.tasks import update_employee_security_score

from ..enums import EmailDeliveryTypes, PhishingActions
from ..tasks import phishing_campaign_send_email_task
from .phishing_template import PhishingTemplate


class PhishingCampaign(BaseModel):
    campaign = models.OneToOneField(
        Campaign, on_delete=models.CASCADE, related_name="phishing_campaign"
    )
    phishing_templates = models.ManyToManyField(
        PhishingTemplate, related_name="phishing_campaigns"
    )
    employees = models.ManyToManyField(
        "users.Employee",
        related_name="phishing_campaigns",
        blank=True,
        through="EmployeePhishingCampaign",
    )
    email_delivery_type = models.CharField(
        max_length=256,
        choices=EmailDeliveryTypes.choices,
        default=EmailDeliveryTypes.IMMEDIATELY,
    )
    email_delivery_date = models.DateTimeField(
        ("Email Delivery Date"), null=True, blank=True
    )
    email_delivery_start_date = models.DateTimeField(
        ("Email Delivery Start Date"), null=True, blank=True
    )
    email_delivery_end_date = models.DateTimeField(
        ("Email Delivery Start Date"), null=True, blank=True
    )

    def cancel(self):
        employee_background_task_ids = self.employee_records.all().values_list(
            "background_task_id", flat=True
        )
        app.control.revoke(employee_background_task_ids, terminate=True)

    @cache
    def departments(self, mapping=False):
        departments_mapping = collections.defaultdict(models.QuerySet[Employee])
        organization = self.campaign.organization
        departments = organization.departments.all()
        for department in departments:
            departments_mapping[department] = Employee.objects.filter(
                emp_profile__department=department
            )

        if mapping:
            return departments_mapping
        return departments_mapping.keys()

    def __str__(self):
        return f"{self.campaign} - {self.id}"

    def filtered_employee_records_by_phishing_template(self, phishing_template_id):
        if not phishing_template_id:
            return self.employee_records.all()
        return self.employee_records.filter(phishing_template_id=phishing_template_id)

    @cache
    def compromised_employees_activity(
        self, phishing_template_id: str | None = None
    ) -> CampaignActivity:
        employee_records = self.filtered_employee_records_by_phishing_template(
            phishing_template_id
        )
        return {
            "completed": employee_records.filter(is_compromised=True).count(),
            "total": employee_records.count(),
        }

    @cache
    def reported_employees_activity(
        self, phishing_template_id: str | None = None
    ) -> CampaignActivity:
        employee_records = self.filtered_employee_records_by_phishing_template(
            phishing_template_id
        )
        return {
            "completed": employee_records.filter(is_reported=True).count(),
            "total": employee_records.count(),
        }

    @cache
    def opened_employees_activity(
        self, phishing_template_id: str | None = None
    ) -> CampaignActivity:
        employee_records = self.filtered_employee_records_by_phishing_template(
            phishing_template_id
        )
        return {
            "completed": employee_records.filter(is_opened=True).count(),
            "total": employee_records.count(),
        }

    @cache
    def clicked_employees_activity(
        self, phishing_template_id: str | None = None
    ) -> CampaignActivity:
        employee_records = self.filtered_employee_records_by_phishing_template(
            phishing_template_id
        )
        return {
            "completed": employee_records.filter(is_clicked=True).count(),
            "total": employee_records.count(),
        }

    @property
    def activity(self) -> CampaignActivity:
        return {
            "completed": self.employee_records.filter(is_opened=True).count(),
            "total": self.employees.count(),
        }

    @cache
    def average_security_score(self, phishing_template_id: str | None = None) -> float:
        return PhishingSecurityScoreToolbox(
            self, phishing_template_id=phishing_template_id
        ).handle()

    @cache
    def top_performers(
        self, phishing_template_id: str | None = None
    ) -> models.QuerySet["EmployeePhishingCampaign"]:
        employee_records = self.employee_records
        if phishing_template_id:
            employee_records = employee_records.filter(
                phishing_template_id=phishing_template_id
            )

        employees_that_reported = employee_records.filter(
            is_opened=True, action=PhishingActions.REPORTED
        )
        employees_that_opened = employee_records.filter(
            is_opened=True, action=PhishingActions.OPENED
        )
        if employees_that_reported.count() > 0:
            return employees_that_reported[:10]
        else:
            return employees_that_opened[:10]

    def update_campaign_dates(self):
        """update camapign dates based on phishing campaign dates"""
        now = timezone.now()
        if self.email_delivery_type == EmailDeliveryTypes.IMMEDIATELY:
            self.email_delivery_date = now
            self.email_delivery_start_date = now
            self.save()
            self.campaign.start_date = now
        elif self.email_delivery_type == EmailDeliveryTypes.SCHEDULED:
            self.campaign.start_date = self.email_delivery_date
            self.campaign.end_date = None
        elif self.email_delivery_type == EmailDeliveryTypes.SCHEDULED_RANGE:
            self.campaign.start_date = self.email_delivery_start_date
            self.campaign.end_date = self.email_delivery_end_date
        self.campaign.save()

    def start(self):
        campaign = self.campaign
        campaign.status = CampaignStatus.ACTIVE
        campaign.save()

    def initiate_phishing_campaign(self):
        match self.email_delivery_type:
            case EmailDeliveryTypes.IMMEDIATELY:
                self.start()
                new_time = timezone.now() + timedelta(minutes=random.randint(1, 5))
                for employee in self.employees.all():
                    new_time += timedelta(minutes=random.randint(1, 5))
                    employee_phishing_campaign = EmployeePhishingCampaign.objects.get(
                        employee=employee, phishing_campaign=self
                    )
                    background_task = phishing_campaign_send_email_task.apply_async(
                        args=[employee.email, self.id], eta=new_time
                    )
                    employee_phishing_campaign.background_task_id = background_task.id
                    employee_phishing_campaign.save()

            case EmailDeliveryTypes.SCHEDULED:
                campaign: Campaign = self.campaign
                background_task = start_campaign.apply_async(
                    args=[campaign.id], eta=self.email_delivery_date
                )
                campaign.background_task_ids.append(background_task.id)
                campaign.save()

                for employee in self.employees.all():
                    employee_phishing_campaign = EmployeePhishingCampaign.objects.get(
                        employee=employee, phishing_campaign=self
                    )
                    background_task = phishing_campaign_send_email_task.apply_async(
                        args=[employee.email, self.id], eta=self.email_delivery_date
                    )
                    employee_phishing_campaign.background_task_id = background_task.id
                    employee_phishing_campaign.save()

            case EmailDeliveryTypes.SCHEDULED_RANGE:
                start_date = self.email_delivery_start_date
                end_date = self.email_delivery_end_date
                campaign: Campaign = self.campaign

                background_task = start_campaign.apply_async(
                    args=[campaign.id], eta=start_date
                )
                campaign.background_task_ids.append(background_task.id)
                campaign.save()

                for employee in self.employees.all():
                    employee_phishing_campaign = EmployeePhishingCampaign.objects.get(
                        employee=employee, phishing_campaign=self
                    )
                    background_task = phishing_campaign_send_email_task.apply_async(
                        args=[employee.email, self.id],
                        eta=start_date + (end_date - start_date) * random.random(),
                    )
                    employee_phishing_campaign.background_task_id = background_task.id
                    employee_phishing_campaign.save()


class EmployeePhishingCampaign(BaseModel):
    employee = models.ForeignKey(
        "users.Employee",
        on_delete=models.CASCADE,
        related_name="phishing_campaign_records",
    )
    phishing_campaign = models.ForeignKey(
        "PhishingCampaign",
        on_delete=models.CASCADE,
        related_name="employee_records",
    )
    phishing_template = models.ForeignKey(
        PhishingTemplate,
        on_delete=models.SET_NULL,
        related_name="employee_records",
        null=True,
        blank=True,
    )
    opened_at = models.DateTimeField(default=None, null=True, blank=True)
    clicked_at = models.DateTimeField(default=None, null=True, blank=True)
    compromised_at = models.DateTimeField(default=None, null=True, blank=True)
    email_sent_at = models.DateTimeField(default=None, null=True, blank=True)
    reported_at = models.DateTimeField(default=None, null=True, blank=True)
    is_email_sent = models.BooleanField(default=False)
    is_opened = models.BooleanField(default=False)
    is_clicked = models.BooleanField(default=False)
    is_compromised = models.BooleanField(default=False)
    is_reported = models.BooleanField(default=False)
    action = models.CharField(
        "Highest Action based on risk rating",
        max_length=256,
        default=PhishingActions.NO_ACTION,
        choices=PhishingActions.choices,
    )
    security_score = models.FloatField(null=True, blank=True)
    background_task_id = models.CharField(max_length=256, null=True, blank=True)

    def get_phishing(self) -> PhishingTemplate:
        if self.phishing_template:
            if self.phishing_campaign.phishing_templates.filter(
                id=self.phishing_template.id
            ).exists():
                return self.phishing_template

        self.phishing_template = random.choice(
            self.phishing_campaign.phishing_templates.all()
        )
        self.save()
        return self.phishing_template

    def open_email(self):
        self.is_opened = True
        self.opened_at = timezone.now()
        self.action = PhishingActions.OPENED
        self.security_score = PhishingSecurityScoreToolbox(
            self.phishing_campaign
        ).phishing_actions_to_score(self.action)
        self.save()
        update_employee_security_score.delay(self.employee.id)

    def click_link(self):
        self.is_clicked = True
        self.clicked_at = timezone.now()
        self.action = PhishingActions.CLICKED
        self.security_score = PhishingSecurityScoreToolbox(
            self.phishing_campaign
        ).phishing_actions_to_score(self.action)
        self.save()
        update_employee_security_score.delay(self.employee.id)

    def compromise(self):
        self.is_compromised = True
        self.compromised_at = timezone.now()
        self.action = PhishingActions.COMPROMISED
        self.security_score = PhishingSecurityScoreToolbox(
            self.phishing_campaign
        ).phishing_actions_to_score(self.action)
        self.save()
        update_employee_security_score.delay(self.employee.id)

    def report(self):
        self.is_reported = True
        self.reported_at = timezone.now()
        self.action = PhishingActions.REPORTED
        self.security_score = PhishingSecurityScoreToolbox(
            self.phishing_campaign
        ).phishing_actions_to_score(self.action)
        self.save()
        update_employee_security_score.delay(self.employee.id)

    def email_sent(self):
        self.is_email_sent = True
        self.email_sent_at = timezone.now()
        self.action = PhishingActions.NO_ACTION
        self.security_score = PhishingSecurityScoreToolbox(
            self.phishing_campaign
        ).phishing_actions_to_score(self.action)
        self.save()
        update_employee_security_score.delay(self.employee.id)

    def delete(self, using=None, keep_parents=False):
        if self.background_task_id:
            app.control.revoke(self.background_task_id, terminate=True)
        return super().delete(using, keep_parents)
