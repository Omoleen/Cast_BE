from django.db import models
from django.utils import timezone
from rest_framework import serializers

from abstract.managers import SimpleModelManager
from campaign.models import Campaign
from content.models import Content
from courses.models import (
    Course,
    CourseCampaign,
    CourseCampaignCourse,
    EmployeeCourseCampaign,
)
from courses.tasks import complete_course_campaign_course_task
from quiz.enums import QuestionTypes
from quiz.models import Question, QuestionOption
from users.enums import EmployeeStatuses
from users.models import Employee

from ..serializers import (
    EmployeeLeaderboardSerializer,
    OngoingEmployeeCampaignSerializer,
    UserTimeSeriesCompletedCoursesSerializer,
    UserTimeSeriesSecurityScoreSerializer,
)


class EmployeeCompleteRegistrationManager(SimpleModelManager):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = Employee
        fields = ["email", "confirm_password", "password"]

        extra_kwargs = {"email": {"read_only": True}}

    def _validate_fields(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return super()._validate_fields(attrs)

    def _update(self, instance, validated_data):
        employee = instance
        employee_profile = employee.emp_profile
        employee_profile.status = EmployeeStatuses.ACTIVE
        employee_profile.save()
        employee.set_password(validated_data["password"])
        employee.save()
        return instance

    def _to_representation(self, instance):
        if self.context["request"].method == "GET":
            return super()._to_representation(instance)
        return "Employee account activated successfully"


class EmployeesAnswerCourseCampaignQuestionManager(SimpleModelManager):
    answer_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True)

    class Meta:
        model = Question
        fields = [
            "answer_ids",
        ]

    def _validate_db(self, attrs):
        course = attrs["course"] = self.context["course"]
        question = attrs["question"] = self.instance
        content = attrs["content"] = self.context["content"]
        course_campaign = self.context["course_campaign"]
        campaign = self.context["campaign"]

        employee = self.context["request"].user
        employee_course_campaign = EmployeeCourseCampaign.objects.get(
            employee=employee, course_campaign=course_campaign
        )
        answers = QuestionOption.objects.filter(
            id__in=attrs["answer_ids"], question=question
        )

        if not employee_course_campaign:
            raise serializers.ValidationError("You were not enrolled into this course")

        if not employee_course_campaign.is_active:
            raise serializers.ValidationError(
                "You can't take any action on this course"
            )

        if not answers.exists():
            raise serializers.ValidationError("Answer not found")

        if question.type == QuestionTypes.SINGLECHOICE and len(answers) > 1:
            raise serializers.ValidationError("Single choice question")
        elif (
            question.type == QuestionTypes.MULTICHOICE
            and len(answers) > question.options.count()
        ):
            raise serializers.ValidationError(
                "answers are morve than the available options"
            )

        self.question = question
        self.answers = answers
        self.course = course
        self.content = content
        self.employee_course_campaign = employee_course_campaign
        self.course_campaign = course_campaign
        self.campaign = campaign
        return attrs

    def _update(self, instance, validated_data):
        employee: Employee = self.context["request"].user
        content: Content = self.content
        question: Question = instance
        answers: models.QuerySet[QuestionOption] = self.answers
        course: Course = self.course
        course_campaign: CourseCampaign = self.course_campaign
        campaign = self.campaign

        content, question, answers, course, course_campaign, campaign

        employee.answer_course_campaign_content_question(
            content=content,
            question=question,
            answers=answers,
            course=course,
            course_campaign=course_campaign,
        )
        complete_course_campaign_course_task.delay(
            employee_id=employee.id,
            course_id=course.id,
            course_campaign_id=course_campaign.id,
        )

        return instance

    def _to_representation(self, instance):
        return "Campaign Question Answered Successfully"


class EmployeesCompleteCourseCampaignContentManager(SimpleModelManager):
    class Meta:
        model = Content
        fields = []

    def _validate_db(self, attrs):
        course = attrs["course"] = self.context["course"]
        content = attrs["content"] = self.instance
        course_campaign = self.context["course_campaign"]
        campaign = self.context["campaign"]

        employee = self.context["request"].user
        employee_course_campaign = EmployeeCourseCampaign.objects.get(
            employee=employee, course_campaign=course_campaign
        )

        if not employee_course_campaign:
            raise serializers.ValidationError("You were not enrolled into this course")

        if not employee_course_campaign.is_active:
            raise serializers.ValidationError(
                "You can't take any action on this course"
            )

        course_campaign_course = course_campaign.campaign_courses.filter(
            employee=employee, course=course
        ).first()

        if not course_campaign_course:
            raise serializers.ValidationError("You were not enrolled into this course")

        if content.has_questions:
            raise serializers.ValidationError("This content has questions")

        self.course = course
        self.content = content
        self.employee_course_campaign = employee_course_campaign
        self.course_campaign_course = course_campaign_course
        self.course_campaign = course_campaign
        self.campaign = campaign
        return attrs

    def _update(self, instance, validated_data):
        employee: Employee = self.context["request"].user
        content: Content = self.content
        course: Course = self.course
        course_campaign: CourseCampaign = self.course_campaign
        course_campaign_course: CourseCampaignCourse = self.course_campaign_course

        employee.complete_course_campaign_content(
            content=content,
            course=course,
            course_campaign=course_campaign,
            course_campaign_course=course_campaign_course,
        )
        complete_course_campaign_course_task.delay(
            employee_id=employee.id,
            course_id=course.id,
            course_campaign_id=course_campaign.id,
        )

        return instance

    def _to_representation(self, instance):
        return "Content completed successfully"


class EmployeesCompleteCourseCampaignManager(SimpleModelManager):
    class Meta:
        model = Campaign
        fields = []

    def _validate_db(self, attrs):
        campaign = self.instance
        course_campaign = campaign.course_campaign

        employee = self.context["request"].user
        employee_course_campaign = EmployeeCourseCampaign.objects.get(
            employee=employee, course_campaign=course_campaign
        )

        if not employee_course_campaign:
            raise serializers.ValidationError("You were not enrolled into this course")

        if not employee_course_campaign.is_active:
            raise serializers.ValidationError(
                "You can't take any action on this course"
            )

        self.employee_course_campaign = employee_course_campaign
        self.course_campaign = course_campaign
        self.campaign = campaign
        return attrs

    def _update(self, instance, validated_data):

        employee_course_campaign = self.employee_course_campaign

        employee_course_campaign.complete()

        return instance


class EmployeeDashboardManager(SimpleModelManager):
    security_score = serializers.SerializerMethodField()
    progress_rate = serializers.SerializerMethodField()
    employees_leaderboard = EmployeeLeaderboardSerializer(many=True)
    ongoing_employee_campaign = OngoingEmployeeCampaignSerializer()
    security_score_timeseries_last_30_days = UserTimeSeriesSecurityScoreSerializer(
        many=True
    )
    courses_completed_timeseries_last_30_days = (
        UserTimeSeriesCompletedCoursesSerializer(many=True)
    )
    security_score_timeseries_last_7days = UserTimeSeriesSecurityScoreSerializer(
        many=True
    )
    courses_completed_timeseries_last_7days = UserTimeSeriesCompletedCoursesSerializer(
        many=True
    )

    class Meta:
        model = Employee
        fields = [
            "active_campaigns_count",
            "completed_campaigns_count",
            "phishing_reported_count",
            "security_score",
            "employees_leaderboard",
            "progress_rate",
            "ongoing_employee_campaign",
            "security_score_timeseries_last_30_days",
            "courses_completed_timeseries_last_30_days",
            "security_score_timeseries_last_7days",
            "courses_completed_timeseries_last_7days",
        ]

    def get_security_score(self, obj) -> None | float:
        return obj.emp_profile.security_score

    def get_progress_rate(self, obj):
        return obj.progress_rate


class EmployeeLearningResourceManager(SimpleModelManager):
    class Meta:
        model = Employee
        fields = ["learning_resources"]
