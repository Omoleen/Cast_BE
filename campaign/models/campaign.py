from functools import cached_property

import pendulum
from django.db import models
from django.utils import timezone

# from content.models import Content
from pendulum import Duration

from abstract.models import BaseModel
from abstract.toolboxes import PendulumToolbox
from campaign.typed_dicts import CampaignActivity
from Castellum.celery import app
from users.models import Department, Employee, Organization

from ..enums import CampaignStatus, CampaignTypes


class Campaign(BaseModel):
    organization = models.ForeignKey(
        Organization,
        to_field="id",
        on_delete=models.CASCADE,
        related_name="org_campaigns",
    )
    name = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=256, choices=CampaignTypes.choices)
    status = models.CharField(
        max_length=256, choices=CampaignStatus.choices, default=CampaignStatus.DRAFT
    )
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    last_step_completed = models.IntegerField(default=0)
    automatically_enroll_employees = models.BooleanField(default=False)

    background_task_ids = models.JSONField(default=list, null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

    @property
    def expiry(self):
        now = timezone.now()
        end_date = self.end_date
        if not end_date:
            return "No end date set"
        duration_in_words = PendulumToolbox.convert_timedelta_to_duration(
            end_date - now, in_words=True
        )
        return duration_in_words.split(",")[0] + " left"

    def set_employees(self, employees):
        campaign = self
        if campaign.is_course_campaign:
            course_campaign = campaign.course_campaign
            course_campaign.employees.set(employees)
        elif campaign.is_phishing_campaign:
            phishing_campaign = campaign.phishing_campaign
            phishing_campaign.employees.set(employees)

    @property
    def is_completed(self):
        return self.last_step_completed == 4

    @property
    def activity(self) -> CampaignActivity:
        if self.is_phishing_campaign:
            return self.phishing_campaign.activity
        elif self.is_course_campaign:
            return self.course_campaign.activity

    @cached_property
    def is_phishing_campaign(self):
        return hasattr(self, "phishing_campaign")

    @cached_property
    def is_course_campaign(
        self,
    ):
        return hasattr(self, "course_campaign")

    def initiate_campaign(self):
        from courses.models import CourseCampaign
        from phishing.models import PhishingCampaign

        if self.is_phishing_campaign:
            phishing_campaign: PhishingCampaign = self.phishing_campaign
            if phishing_campaign:
                phishing_campaign.update_campaign_dates()
                phishing_campaign.initiate_phishing_campaign()
        elif self.is_course_campaign:
            course_campaign: CourseCampaign = self.course_campaign
            if course_campaign:
                course_campaign.initiate_course_campaign()

    def revoke_background_tasks(self):
        for task_id in self.background_task_ids:
            app.control.revoke(task_id, terminate=True)
        self.background_task_ids = []

    def cancel(self):
        self.revoke_background_tasks()
        self.status = CampaignStatus.CANCELLED
        if self.is_phishing_campaign:
            self.phishing_campaign.cancel()
        elif self.is_course_campaign:
            self.course_campaign.cancel()
        self.save()

    def delete(self, *args, **kwargs):
        # self.revoke_background_tasks()
        self.cancel()
        return super().delete(*args, **kwargs)
