from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import models

from Castellum.enums import Roles
from users.services import UserImport

from .models import (
    Department,
    DepartmentTimeSeriesSecurityScore,
    Employee,
    Organization,
    UserCourse,
    UserTimeSeriesCompletedCourses,
    UserTimeSeriesSecurityScore,
)

User = get_user_model()


@shared_task(name="Create Employee Records on import")
def create_employee_records(records: list[str], org_id: str):
    org = Organization.objects.get(id=org_id)
    user_import = UserImport(organization=org, records=records)
    user_import.create_records()

    for employee in user_import.new_employees:
        employee.receive_email("employee-invite")

    return user_import.new_employees


@shared_task(name="Update Employee Phishing Score")
def update_employee_security_score(employee_id: str):
    from phishing.models import EmployeePhishingCampaign

    employee = Employee.objects.get(id=employee_id)
    employee_phishing_campaigns = EmployeePhishingCampaign.objects.filter(
        employee=employee
    ).aggregate(
        average_security_score=models.Avg("security_score"),
    )
    employee.emp_profile.security_score = employee_phishing_campaigns.get(
        "average_security_score"
    )
    employee.emp_profile.save()

    department = employee.emp_profile.department
    department_employees = Employee.objects.filter(
        emp_profile__department=department
    ).aggregate(average_security_score=models.Avg("emp_profile__security_score"))
    department.security_score = department_employees.get("average_security_score")
    department.save()
    organization = department.organization
    organization_employees = Employee.objects.filter(
        emp_profile__organization=organization
    ).aggregate(average_security_score=models.Avg("emp_profile__security_score"))
    organization.org_profile.security_score = organization_employees.get(
        "average_security_score"
    )
    organization.org_profile.save()


@shared_task(name="Store security scores and courses completed at the end of the day")
def store_security_scores_and_courses_completed():
    users = User.objects.all()
    departments = Department.objects.all()
    users_security_score_timeseries = []
    users_courses_completed_timeseries = []
    departments_timeseries = []
    for user in users:
        if user.role == Roles.ORGANIZATION:
            profile = user.org_profile
        elif user.role == Roles.EMPLOYEE:
            profile = user.emp_profile
        else:
            continue
        users_security_score_timeseries.append(
            UserTimeSeriesSecurityScore(
                user=user, security_score=profile.security_score
            )
        )
        users_courses_completed_timeseries.append(
            UserTimeSeriesCompletedCourses(
                user=user,
                courses_completed=UserCourse.objects.filter(
                    user=user, is_completed=True
                ).count(),
            )
        )
    for department in departments:
        departments_timeseries.append(
            DepartmentTimeSeriesSecurityScore(
                department=department, security_score=department.security_score
            )
        )
    UserTimeSeriesSecurityScore.objects.bulk_create(users_security_score_timeseries)
    UserTimeSeriesCompletedCourses.objects.bulk_create(
        users_courses_completed_timeseries
    )
    DepartmentTimeSeriesSecurityScore.objects.bulk_create(departments_timeseries)
