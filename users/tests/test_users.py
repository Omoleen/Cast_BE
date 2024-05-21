from unittest.mock import patch
from uuid import uuid4

from faker import Faker

from abstract.base_test import BaseTestCase
from abstract.tasks import send_email
from Castellum.enums import Roles
from users.enums import EmployeeStatuses
from users.factory import DepartmentFactory, EmployeeFactory, OrganizationFactory
from users.models import Department, User

SIGNUP_1 = "/api/users/register/"
SIGNUP_2 = "/api/users/register-2/"
EMPLOYEES = "/api/users/employees/"
ADD_EMPLOYEE = "/api/users/add-employee/"
DEACTIVATE_EMPLOYEE = "/api/users/employees/deactivate/"
DEPARTMENT = "/api/users/departments/"
get_update_employee_path = lambda id: f"/api/users/employees/{id}/"
get_department_path = lambda id: f"/api/users/departments/{id}/"
get_search_employees_path = lambda name: f"/api/users/employees/?query={name}"


class TestUser(BaseTestCase):
    @patch.object(send_email, "delay")
    def test_organization_signup(self, send_email):
        fake = Faker()
        email = fake.email()

        data = {"email": email, "name": fake.company(), "url": fake.url()}
        response = self.client.post(SIGNUP_1, data=data)

        self.assertCreated(response)
        send_email.assert_called_once()

        org = User.objects.filter(email=data["email"]).first()
        if not org:
            self.fail("Organization not created")

        self.assertEqual(org.role, Roles.ORGANIZATION)
        self.assertEqual(org.org_profile.name, data["name"])
        self.assertEqual(org.org_profile.url, data["url"])
        self.assertFalse(org.is_active)
        self.assertFalse(org.is_email_verified)
        token = org.token
        password = fake.password()
        data = {
            "email": email,
            "password": password,
            "token": token,
            "confirmPassword": password,
        }
        response = self.client.post(SIGNUP_2, data=data)
        self.assertCreated(response)
        org.refresh_from_db()
        self.assertTrue(org.is_active)
        self.assertTrue(org.is_email_verified)
        send_email.assert_called_once()

    @patch.object(send_email, "delay")
    def test_organization_signup_wrong_token(self, send_email):
        fake = Faker()
        email = fake.email()

        data = {"email": email, "name": fake.company(), "url": fake.url()}
        response = self.client.post(SIGNUP_1, data=data)

        self.assertCreated(response)
        send_email.assert_called_once()

        org = User.objects.filter(email=data["email"]).first()
        if not org:
            self.fail("Organization not created")

        self.assertEqual(org.role, Roles.ORGANIZATION)
        self.assertEqual(org.org_profile.name, data["name"])
        self.assertEqual(org.org_profile.url, data["url"])
        self.assertFalse(org.is_active)
        self.assertFalse(org.is_email_verified)
        token = org.token[::-1]
        password = fake.password()
        data = {
            "email": email,
            "password": password,
            "token": token,
            "confirmPassword": password,
        }
        response = self.client.post(SIGNUP_2, data=data)
        self.assert_bad(response)

    def test_get_employees_response(self):
        self.client.force_authenticate(self.organization)
        response = self.client.get(EMPLOYEES)
        self.assert_ok(response)
        self.assertEqual(len(response.data), 1)

    @patch.object(send_email, "delay")
    def test_add_employees_response(self, send_email):
        fake = Faker()
        data = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "department_id": self.department.id,
            "email": fake.email(),
            "password": fake.password(),
        }

        self.client.force_authenticate(self.organization)
        response = self.client.post(ADD_EMPLOYEE, data=data)
        self.assertCreated(response)
        send_email.assert_called_once()

    @patch.object(send_email, "delay")
    def test_add_employees_no_department_response(self, send_email):
        fake = Faker()
        data = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "password": fake.password(),
        }

        self.client.force_authenticate(self.organization)
        response = self.client.post(ADD_EMPLOYEE, data=data)
        self.assertCreated(response)
        send_email.assert_called_once()

    def test_add_employees_wrong_department_response(self):
        fake = Faker()
        data = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "password": fake.password(),
            "department_id": uuid4(),
        }

        self.client.force_authenticate(self.organization)
        response = self.client.post(ADD_EMPLOYEE, data=data)
        self.assert_bad(response)

    def test_deactivate_employee_response(self):
        self.client.force_authenticate(self.organization)
        data = {"ids": [self.employee.id]}
        response = self.client.post(DEACTIVATE_EMPLOYEE, data=data)
        self.assertCreated(response)
        self.employee.refresh_from_db()
        self.assertFalse(self.employee.is_active)
        self.assertEqual(self.employee.emp_profile.status, EmployeeStatuses.DEACTIVATED)

    def test_deactivate_unknown_employee_response(self):
        self.client.force_authenticate(self.organization)
        data = {"ids": [uuid4()]}
        response = self.client.post(DEACTIVATE_EMPLOYEE, data=data)
        self.assert_bad(response)

    def test_deactivate_good_and_non_existing_employees_response(self):
        self.client.force_authenticate(self.organization)
        data = {"ids": [uuid4(), self.employee.id]}
        response = self.client.post(DEACTIVATE_EMPLOYEE, data=data)
        self.assertCreated(response)

    def test_update_employee(self):
        self.client.force_authenticate(self.organization)
        dep = DepartmentFactory(organization=self.organization)
        fake = Faker()
        data = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "department_id": dep.id,
        }

        first_name, last_name = (
            self.employee.emp_profile.first_name,
            self.employee.emp_profile.last_name,
        )
        response = self.client.patch(
            get_update_employee_path(self.employee.id), data=data
        )
        self.assert_ok(response)
        response_data = response.json()["data"]
        self.assertNotEqual(first_name, response_data["emp_profile"]["first_name"])
        self.assertNotEqual(last_name, response_data["emp_profile"]["last_name"])
        self.assertNotEqual(
            self.department.id, response_data["emp_profile"]["department"]["id"]
        )
        self.assertEqual(data["first_name"], response_data["emp_profile"]["first_name"])
        self.assertEqual(data["last_name"], response_data["emp_profile"]["last_name"])
        self.assertEqual(
            str(data["department_id"]), response_data["emp_profile"]["department"]["id"]
        )

    def test_search_employees(self):
        self.client.force_authenticate(self.organization)
        response = self.client.get(
            get_search_employees_path(self.employee.emp_profile.first_name[0])
        )
        self.assert_ok(response)
        self.assertEqual(len(response.data), 1)

    def test_search_employees_no_employee(self):
        self.client.force_authenticate(self.organization)
        response = self.client.get(get_search_employees_path("test"))
        self.assert_ok(response)
        self.assertEqual(len(response.data), 0)

    def test_search_employees_using_department(self):
        self.client.force_authenticate(self.organization)
        response = self.client.get(get_search_employees_path(self.department.name))
        self.assert_ok(response)
        self.assertEqual(len(response.data), 1)
