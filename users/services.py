from django.db import models

from users.models import Department, Employee, EmployeeProfile, Organization


class UserImport:
    def __init__(self, records: list[dict], organization: Organization):
        self.records = records
        self.organization = organization
        self.new_employees = []

    def create_records(self):
        records = self.records
        organization = self.organization
        registered_employees = []

        flattened_records = [record["email"] for record in records]
        registered_employees = Employee.objects.prefetch_related("emp_profile").filter(
            email__in=flattened_records,
            # emp_profile__organization=organization
        )
        new_employees = []
        for record in records:
            employee = registered_employees.filter(email=record["email"])
            department = None
            if record.get("department"):
                department = Department.objects.filter(
                    name=record.get("department").lower(), organization=organization
                ).first()
                if not department:
                    department = Department.objects.create(
                        name=record.get("department").lower(), organization=organization
                    )
            if employee.exists():
                employee = employee.first()
                profile = employee.emp_profile
                profile.department = department
                profile.first_name = record["first_name"]
                profile.last_name = record["last_name"]
                profile.save()
            else:
                employee = Employee.objects.create_emp(
                    email=record["email"],
                    first_name=record["first_name"],
                    last_name=record["last_name"],
                    organization=organization,
                    department=department,
                )
                new_employees.append(employee)
        self.new_employees = new_employees
