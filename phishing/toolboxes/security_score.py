from django.db import models
from django.db.models import Case, IntegerField, Value, When

from users.models import Department, Employee, Organization, User

from ..enums import PhishingActions


class PhishingSecurityScoreToolbox:
    def __init__(
        self, phishing_campaign, average=True, obj=None, phishing_template_id=None
    ):
        self.phishing_campaign = phishing_campaign
        self.obj = obj
        self.average = average
        self.phishing_template_id = phishing_template_id

    def phishing_actions_to_score(self, action):
        mapping = {
            PhishingActions.COMPROMISED: 0,
            PhishingActions.CLICKED: 30,
            PhishingActions.OPENED: 70,
            PhishingActions.REPORTED: 100,
        }
        return mapping.get(action)

    def calculate_score(self, employees_records):
        if isinstance(employees_records, models.QuerySet):
            temp_score = 0
            count = employees_records.count()
            if not count:
                return count
            for record in employees_records:
                score = self.phishing_actions_to_score(record.action)
                if score is not None:
                    temp_score += score
                else:
                    count -= 1
            if self.average and count:
                return temp_score / count
            return temp_score
        elif isinstance(employees_records, Employee):
            return self.phishing_actions_to_score(employees_records.action)

    def handle(self) -> float:
        obj = self.obj
        if obj is None:
            return self.calculate_campaign_score()
        elif isinstance(obj, Department):
            return self.calculate_department_score(obj)
        elif isinstance(obj, Employee):
            return self.calculate_employee_score(obj)
        elif isinstance(obj, models.QuerySet[Employee]):
            return self.calculate_employees_score(obj)
        return 0

    def calculate_campaign_score(self):
        filters = {
            "is_opened": True,
        }
        if self.phishing_template_id:
            filters["phishing_template_id"] = self.phishing_template_id
        employees_records = self.phishing_campaign.employee_records.filter(**filters)
        return self.calculate_score(employees_records)

    def calculate_department_score(self, department: Department):
        employees_records = self.phishing_campaign.employee_records.filter(
            is_opened=True, employee__emp_profile__department=department
        ).exclude(action=PhishingActions.NO_ACTION)
        return self.calculate_score(employees_records)

    def calculate_employee_score(self, employee: Employee):
        employees_records = self.phishing_campaign.employee_records.filter(
            is_opened=True, employee=employee
        )
        return self.calculate_score(employees_records)

    def calculate_employees_score(self, employees: models.QuerySet[Employee]):
        employees_records = self.phishing_campaign.employee_records.filter(
            is_opened=True, employee__in=employees
        )
        return self.calculate_score(employees_records)
