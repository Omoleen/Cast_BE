import collections

from django.db import models
from django.urls import resolve
from rest_framework import serializers

from abstract.managers import SimpleManager, SimpleModelManager
from campaign.typed_dicts import CampaignActivity
from phishing.toolboxes import PhishingSecurityScoreToolbox
from phishing.typed_dicts import DepartmentScore, EmployeeScores
from users.models import Employee
from users.serializers import EmployeeSerializer

from .enums import PhishingActions
from .models import EmployeePhishingCampaign, PhishingCampaign, PhishingTemplate


class PhishingTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhishingTemplate
        fields = [
            "id",
            "organization",
            "name",
            "description",
            "vendor",
        ]


class PhishingCampaignEmployeeRecordSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="employee.full_name")
    email = serializers.CharField(source="employee.email")
    department = serializers.CharField(source="employee.department.name")
    scores = serializers.SerializerMethodField()
    employee_id = serializers.CharField(source="employee.id")

    class Meta:
        model = EmployeePhishingCampaign
        fields = ["action", "full_name", "email", "department", "scores", "employee_id"]

    def get_scores(self, obj) -> EmployeeScores:
        security_score_toolbox = PhishingSecurityScoreToolbox(self)
        security_score = security_score_toolbox.phishing_actions_to_score(obj.action)
        if security_score is not None:
            risk_rating = (100 - security_score) / 100
            return EmployeeScores(
                security_score=security_score, risk_rating=risk_rating
            )
        return EmployeeScores(security_score="N/A", risk_rating="N/A")


class PhishingCampaignTopPerformersRecordSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="employee.full_name")
    department = serializers.CharField(source="employee.department.name")

    class Meta:
        model = EmployeePhishingCampaign
        fields = [
            "full_name",
            "department",
        ]


class PhishingCampaignSerializer(serializers.ModelSerializer):
    employee_records = PhishingCampaignEmployeeRecordSerializer(
        many=True, read_only=True
    )
    top_performers = serializers.SerializerMethodField()
    scores = serializers.SerializerMethodField()
    compromised_employees_activity = serializers.SerializerMethodField()
    reported_employees_activity = serializers.SerializerMethodField()
    opened_employees_activity = serializers.SerializerMethodField()
    clicked_employees_activity = serializers.SerializerMethodField()
    average_security_score = serializers.SerializerMethodField()
    phishing_templates = PhishingTemplateSerializer(read_only=True, many=True)

    class Meta:
        model = PhishingCampaign
        fields = [
            "employee_records",
            "compromised_employees_activity",
            "reported_employees_activity",
            "opened_employees_activity",
            "clicked_employees_activity",
            "average_security_score",
            "top_performers",
            "scores",
            "phishing_templates",
            "email_delivery_type",
            "email_delivery_date",
            "email_delivery_start_date",
            "email_delivery_end_date",
        ]

    def get_average_security_score(self, obj) -> float:
        return obj.average_security_score()

    def get_clicked_employees_activity(self, obj) -> CampaignActivity:
        return obj.clicked_employees_activity()

    def get_opened_employees_activity(self, obj) -> CampaignActivity:
        return obj.opened_employees_activity()

    def get_reported_employees_activity(self, obj) -> CampaignActivity:
        return obj.reported_employees_activity()

    def get_compromised_employees_activity(self, obj) -> CampaignActivity:
        return obj.compromised_employees_activity()

    def get_scores(self, phishing_campaign: PhishingCampaign) -> list[DepartmentScore]:
        departments_to_employees = phishing_campaign.departments(mapping=True)
        departments_scores = []
        self.instance = phishing_campaign

        for department, employees in departments_to_employees.items():
            score = collections.defaultdict(list)
            score["department"] = department.name
            high = self._get_score(
                actions=[PhishingActions.REPORTED, PhishingActions.OPENED],
                employees=employees,
                average=False,
            )
            medium = self._get_score(
                actions=[PhishingActions.CLICKED], employees=employees, average=False
            )
            low = self._get_score(
                actions=[PhishingActions.COMPROMISED],
                employees=employees,
                average=False,
            )
            department_security_score = PhishingSecurityScoreToolbox(
                phishing_campaign, department
            ).handle()
            if department_security_score == 0:
                score["security_score"].append(
                    {
                        "score": 0,
                        "high": 0,
                        "medium": 0,
                        "low": 0,
                    }
                )
                score["risk_rating"].append(
                    {
                        "score": 0,
                        "high": 0,
                        "medium": 0,
                        "low": 0,
                    }
                )
            else:
                high_security_score = (high / department_security_score) * 100
                medium_security_score = (medium / department_security_score) * 100
                low_security_score = (low / department_security_score) * 100
                score["security_score"].append(
                    {
                        "score": department_security_score,
                        "high": high_security_score,
                        "medium": medium_security_score,
                        "low": low_security_score,
                    }
                )
                score["risk_rating"].append(
                    {
                        "score": 100 - department_security_score,
                        "high": 100 - high_security_score,
                        "medium": medium_security_score,
                        "low": 100 - low_security_score,
                    }
                )
            departments_scores.append(score)
        return [
            DepartmentScore(department_score) for department_score in departments_scores
        ]

    def _get_score(self, actions, employees, average):
        filtered_employees_records = self.instance.employee_records.filter(
            employee__in=employees, action__in=actions
        ).exclude(action=PhishingActions.NO_ACTION)
        total_score = PhishingSecurityScoreToolbox(
            self.instance, average=average
        ).calculate_score(filtered_employees_records)
        return (
            total_score / filtered_employees_records.count()
            if filtered_employees_records.count()
            else 0
        )

    def get_top_performers(
        self, obj: PhishingCampaign
    ) -> list[PhishingCampaignTopPerformersRecordSerializer]:
        return PhishingCampaignTopPerformersRecordSerializer(
            obj.top_performers(), many=True
        ).data


class PhishingCampaignDetailedSerializer(serializers.ModelSerializer):
    employee_records = serializers.SerializerMethodField()
    top_performers = serializers.SerializerMethodField()
    scores = serializers.SerializerMethodField()
    compromised_employees_activity = serializers.SerializerMethodField()
    reported_employees_activity = serializers.SerializerMethodField()
    opened_employees_activity = serializers.SerializerMethodField()
    clicked_employees_activity = serializers.SerializerMethodField()
    average_security_score = serializers.SerializerMethodField()
    phishing_templates = PhishingTemplateSerializer(read_only=True, many=True)

    class Meta:
        model = PhishingCampaign
        fields = [
            "employee_records",
            "compromised_employees_activity",
            "reported_employees_activity",
            "opened_employees_activity",
            "clicked_employees_activity",
            "average_security_score",
            "top_performers",
            "scores",
            "phishing_templates",
            "email_delivery_type",
            "email_delivery_date",
            "email_delivery_start_date",
            "email_delivery_end_date",
        ]

    def get_average_security_score(self, obj) -> float:
        return obj.average_security_score(self.context.get("phishing_template_id"))

    def get_clicked_employees_activity(self, obj) -> CampaignActivity:
        return obj.clicked_employees_activity(self.context.get("phishing_template_id"))

    def get_opened_employees_activity(self, obj) -> CampaignActivity:
        return obj.opened_employees_activity(self.context.get("phishing_template_id"))

    def get_reported_employees_activity(self, obj) -> CampaignActivity:
        return obj.reported_employees_activity(self.context.get("phishing_template_id"))

    def get_compromised_employees_activity(self, obj) -> CampaignActivity:
        return obj.compromised_employees_activity(
            self.context.get("phishing_template_id")
        )

    def get_employee_records(
        self, obj
    ) -> list[PhishingCampaignEmployeeRecordSerializer]:
        return PhishingCampaignEmployeeRecordSerializer(
            obj.filtered_employee_records_by_phishing_template(
                self.context.get("phishing_template_id")
            ),
            many=True,
        ).data

    def get_top_performers(
        self, obj: PhishingCampaign
    ) -> list[PhishingCampaignTopPerformersRecordSerializer]:
        return PhishingCampaignTopPerformersRecordSerializer(
            obj.top_performers(self.context.get("phishing_template_id")), many=True
        ).data

    def get_scores(self, phishing_campaign: PhishingCampaign) -> list[DepartmentScore]:

        phishing_template_id = self.context.get("phishing_template_id")

        departments_to_employees = phishing_campaign.departments(mapping=True)
        departments_scores = []
        self.instance = phishing_campaign

        for department, employees in departments_to_employees.items():
            employees = employees.filter(
                phishing_campaign_records__phishing_template_id=phishing_template_id,
                phishing_campaign_records__phishing_campaign=self.instance,
            )
            if not employees.exists():
                continue
            score = collections.defaultdict(list)
            score["department"] = department.name
            high = self._get_score(
                actions=[PhishingActions.REPORTED, PhishingActions.OPENED],
                employees=employees,
                average=False,
            )
            medium = self._get_score(
                actions=[PhishingActions.CLICKED], employees=employees, average=False
            )
            low = self._get_score(
                actions=[PhishingActions.COMPROMISED],
                employees=employees,
                average=False,
            )
            department_security_score = PhishingSecurityScoreToolbox(
                phishing_campaign, department
            ).handle()
            if department_security_score == 0:
                score["security_score"].append(
                    {
                        "score": 0,
                        "high": 0,
                        "medium": 0,
                        "low": 0,
                    }
                )
                score["risk_rating"].append(
                    {
                        "score": 0,
                        "high": 0,
                        "medium": 0,
                        "low": 0,
                    }
                )
            else:
                high_security_score = (high / department_security_score) * 100
                medium_security_score = (medium / department_security_score) * 100
                low_security_score = (low / department_security_score) * 100
                score["security_score"].append(
                    {
                        "score": department_security_score,
                        "high": high_security_score,
                        "medium": medium_security_score,
                        "low": low_security_score,
                    }
                )
                score["risk_rating"].append(
                    {
                        "score": 100 - department_security_score,
                        "high": 100 - high_security_score,
                        "medium": medium_security_score,
                        "low": 100 - low_security_score,
                    }
                )
            departments_scores.append(score)
        return [
            DepartmentScore(department_score) for department_score in departments_scores
        ]

    def _get_score(self, actions, employees, average):
        filtered_employees_records = self.instance.employee_records.filter(
            employee__in=employees, action__in=actions
        ).exclude(action=PhishingActions.NO_ACTION)
        total_score = PhishingSecurityScoreToolbox(
            self.instance, average=average
        ).calculate_score(filtered_employees_records)
        return (
            total_score / filtered_employees_records.count()
            if filtered_employees_records.count()
            else 0
        )
