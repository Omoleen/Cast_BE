from unittest.mock import patch

import pendulum
from faker import Faker

from abstract.base_test import BaseTestCase
from abstract.tasks import send_email
from Castellum.enums import LearningTypes, Roles
from courses.models import Course
from users.enums import EmployeeStatuses
from users.models import CompletedContent, Department, User, UserCourse

from ..factory import CourseCampaignFactory

CAMPAIGNS = "/api/campaigns/"
get_create_course_campaign_path = f"{CAMPAIGNS}create/course/"
get_create_phishing_campaign_path = f"{CAMPAIGNS}create/phishing/"
get_edit_course_campaign_step_1_path = f"{CAMPAIGNS}course-campaigns/edit/1/"
get_edit_phishing_campaign_step_1_path = f"{CAMPAIGNS}phishing-campaigns/edit/1/"
get_edit_campaign_step_2_path = f"{CAMPAIGNS}/edit/2/"
get_edit_course_campaign_step_3_path = f"{CAMPAIGNS}course-campaigns/edit/3/"
get_edit_phishing_campaign_step_3_path = f"{CAMPAIGNS}phishing-campaigns/edit/3/"
get_submit_campaign_path = f"{CAMPAIGNS}/submit/"
get_campaigns_path = f"{CAMPAIGNS}"
get_campaign_detail_path = lambda id: f"{CAMPAIGNS}{id}/"


class TestCampaign(BaseTestCase):
    def test_get_campaigns(self):
        self.client.force_authenticate(self.organization)
        response = self.client.get(get_campaigns_path)
        self.assert_ok(response)

    def test_get_campaign_detail(self):
        self.client.force_authenticate(self.organization)
        campaign = CourseCampaignFactory.create(organization=self.organization)
        campaign.set_employees([self.employee])
        response = self.client.get(get_campaign_detail_path(campaign.id))
        self.assert_ok(response)

    def test_create_course_campaign_step_1(self):
        self.client.force_authenticate(self.organization)
        now = pendulum.now()
        data = {
            "name": "Course Campaign",
            "description": "anything",
            "type": "general",
            "start_date": now.add(days=5),
            "end_date": now.add(days=10),
            "automatically_enroll_employees": True,
        }
        response = self.client.post(get_create_course_campaign_path, data=data)
        self.assertCreated(response)

    def test_create_course_campaign_invalid_start_date(self):
        self.client.force_authenticate(self.organization)
        now = pendulum.now()
        data = {
            "name": "Course Campaign",
            "description": "anything",
            "type": "general",
            "start_date": now.subtract(days=5),
            "end_date": now.add(days=10),
            "automatically_enroll_employees": True,
        }
        response = self.client.post(get_create_course_campaign_path, data=data)
        self.assert_bad(response)

    def test_create_course_campaign_invalid_dates(self):
        self.client.force_authenticate(self.organization)
        now = pendulum.now()
        data = {
            "name": "Course Campaign",
            "description": "anything",
            "type": "general",
            "start_date": now.add(days=5),
            "end_date": now.add(days=1),
            "automatically_enroll_employees": True,
        }
        response = self.client.post(get_create_course_campaign_path, data=data)
        self.assert_bad(response)

    def test_create_course_campaign_same_name(self):
        self.client.force_authenticate(self.organization)
        campaign = CourseCampaignFactory.create(organization=self.organization)
        now = pendulum.now()
        data = {
            "name": campaign.name,
            "description": "anything",
            "type": "general",
            "start_date": now.add(days=5),
            "end_date": now.add(days=1),
            "automatically_enroll_employees": True,
        }
        response = self.client.post(get_create_course_campaign_path, data=data)
        self.assert_bad(response)

    # def test_edit_st
