from unittest.mock import patch
from uuid import uuid4

from faker import Faker

from abstract.base_test import BaseTestCase
from abstract.tasks import send_email
from Castellum.enums import Roles
from users.enums import EmployeeStatuses
from users.models import Department, User

SIGNUP_1 = "/api/users/register/"
SIGNUP_2 = "/api/users/register-2/"
EMPLOYEES = "/api/users/employees/"
ADD_EMPLOYEE = "/api/users/add-employee/"
DEACTIVATE_EMPLOYEE = "/api/users/employees/deactivate/"
DEPARTMENT = "/api/users/departments/"
get_department_path = lambda id: f"/api/users/departments/{id}/"
get_search_departments_path = lambda name: f"/api/users/departments/?name={name}"
DELETE_DEPARTMENTS = "/api/users/departments/delete/"


class TestUser(BaseTestCase):
    def test_create_department_response(self):
        self.client.force_authenticate(self.organization)
        data = {"name": "Test Department"}
        response = self.client.post(DEPARTMENT, data=data)
        self.assertCreated(response)
        self.assertEqual(Department.objects.count(), 2)

    def test_create_department_no_name_response(self):
        self.client.force_authenticate(self.organization)
        data = {}
        response = self.client.post(DEPARTMENT, data=data)
        self.assert_bad(response)

    def test_create_department_no_auth_response(self):
        data = {"name": "Test Department"}
        response = self.client.post(DEPARTMENT, data=data)
        self.assertUnAuthorized(response)

    def test_create_department_no_org_response(self):
        self.client.force_authenticate(self.employee)
        data = {"name": "Test Department"}
        response = self.client.post(DEPARTMENT, data=data)
        self.assertForbidden(response)

    def test_get_department_response(self):
        self.client.force_authenticate(self.organization)
        response = self.client.get(DEPARTMENT)
        self.assert_ok(response)
        print(response.json())
        self.assertEqual(len(response.data["results"]), 1)

    def test_delete_department_response(self):
        self.client.force_authenticate(self.organization)
        response = self.client.delete(get_department_path(self.department.id))
        self.assert_no_content(response)
        self.assertEqual(Department.objects.count(), 0)

    def test_delete_unknown_department_response(self):
        self.client.force_authenticate(self.organization)
        response = self.client.delete(get_department_path(uuid4()))
        self.assertNotFound(response)

    def test_delete_department_no_auth_response(self):
        response = self.client.delete(get_department_path(self.department.id))
        self.assertUnAuthorized(response)

    def test_update_department_response(self):
        self.client.force_authenticate(self.organization)
        data = {"name": "New Department"}
        response = self.client.patch(get_department_path(self.department.id), data=data)
        self.assert_ok(response)
        self.department.refresh_from_db()
        self.assertEqual(self.department.name, data["name"].lower())

    def test_update_unknown_department_response(self):
        self.client.force_authenticate(self.organization)
        data = {"name": "New Department"}
        response = self.client.patch(get_department_path(uuid4()), data=data)
        self.assertNotFound(response)

    def test_search_department_no_department_response(self):
        self.client.force_authenticate(self.organization)
        response = self.client.get(get_search_departments_path("test"))
        self.assert_ok(response)
        self.assertEqual(len(response.data["results"]), 0)

    def test_search_department_response(self):
        self.client.force_authenticate(self.organization)
        response = self.client.get(get_search_departments_path(self.department.name[0]))
        self.assert_ok(response)
        self.assertEqual(len(response.data["results"]), 1)

    def test_delete_departments_response(self):
        self.client.force_authenticate(self.organization)
        data = {"ids": [self.department.id]}
        self.assertEqual(Department.objects.count(), 1)
        response = self.client.post(DELETE_DEPARTMENTS, data=data)
        self.assert_ok(response)
        self.assertEqual(Department.objects.count(), 0)

    def test_delete_departments_non_existing_response(self):
        self.client.force_authenticate(self.organization)
        data = {"ids": [uuid4()]}
        self.assertEqual(Department.objects.count(), 1)
        response = self.client.post(DELETE_DEPARTMENTS, data=data)
        self.assert_bad(response)
        self.assertEqual(Department.objects.count(), 1)
