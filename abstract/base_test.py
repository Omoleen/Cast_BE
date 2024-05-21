from datetime import datetime

import factory
import pendulum
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.db.backends.base.base import BaseDatabaseWrapper
from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.test.runner import DiscoverRunner
from rest_framework import status
from rest_framework.test import APIClient

from users.factory import EmployeeFactory, OrganizationFactory

User = get_user_model()


class BaseTestCase(TestCase):

    fixtures = [
        "courses.json",
        "contents.json",
        "course_content.json",
        "questions.json",
        "answers.json",
    ]

    @classmethod
    def setUpClass(cls):
        import django

        django.setup()

        super().setUpClass()

    def get_current_time(self) -> datetime:
        """Get current time"""
        return pendulum.now()

    def get_current_time_as_string(self) -> str:
        """Get current time as string"""
        return datetime.strftime(self.get_current_time(), "%Y-%m-%d %H:%M:%S")

    def setUp(self) -> None:
        self.employee = EmployeeFactory.create()
        self.organization = self.employee.emp_profile.organization
        self.department = self.employee.emp_profile.department
        self.client = APIClient()

    def assert_ok(self, response: HttpResponse) -> bool:
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def assertCreated(self, response: HttpResponse) -> bool:
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def assert_bad(self, response: HttpResponse) -> bool:
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def assert_no_content(self, response: HttpResponse) -> bool:
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def assertForbidden(self, response: HttpResponse) -> bool:
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def assertUnAuthorized(self, response: HttpResponse) -> bool:
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def assertNotFound(self, response: HttpResponse) -> bool:
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
