from django.db.models import Count, Q
from rest_framework import serializers

from abstract.managers import SimpleModelManager
from Castellum.enums import Roles
from content.models.content import Content
from content.serializers import ContentSerializer
from users.models import AnsweredQuestion, Employee, Organization, UserCourse
from users.serializers import EmployeeSerializer

from .models import Course, CourseCampaign, CourseContent


class CourseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "description",
            "learning_type",
            "thumbnail",
            "material_count",
            "quiz_count",
            "questions_count",
            "duration",
        ]


class CampaignCourseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "description",
            "learning_type",
            "thumbnail",
            "material_count",
            "quiz_count",
            "questions_count",
            "duration",
        ]


class CourseCampaignSerializer(serializers.ModelSerializer):
    courses = CampaignCourseListSerializer(read_only=True, many=True)
    employees = EmployeeSerializer(many=True, read_only=True)
    # completion_rate = serializers.SerializerMethodField()
    # average_score = serializers.SerializerMethodField()
    # learners = serializers.SerializerMethodField()

    class Meta:
        model = CourseCampaign
        fields = ["courses", "employees"]


class EmployeeCourseCampaignSerializer(serializers.ModelSerializer):
    courses = CampaignCourseListSerializer(read_only=True, many=True)
    progress = serializers.SerializerMethodField()
    remaining_courses = serializers.SerializerMethodField()
    questions_left = serializers.SerializerMethodField()

    class Meta:
        model = CourseCampaign
        fields = [
            "courses",
            "duration",
            "quiz_count",
            "progress",
            "remaining_courses",
            "questions_left",
        ]

    def get_progress(self, course_campaign: CourseCampaign) -> int:
        employee: Employee = self.context["request"].user
        employee_course_campaign: CourseCampaign = (
            course_campaign.employee_records.filter(employee=employee).first()
        )

        return employee_course_campaign.progress_rate

    def get_remaining_courses(self, course_campaign: CourseCampaign) -> int:
        employee: Employee = self.context["request"].user
        employee_course_campaign: CourseCampaign = (
            course_campaign.employee_records.filter(employee=employee).first()
        )

        return employee_course_campaign.courses_left

    def get_questions_left(self, course_campaign: CourseCampaign) -> int:
        employee: Employee = self.context["request"].user
        employee_course_campaign: CourseCampaign = (
            course_campaign.employee_records.filter(employee=employee).first()
        )

        return employee_course_campaign.questions_left


class CampaignEmployeeSerializer(serializers.ModelSerializer):
    department = serializers.CharField()

    class Meta:
        model = Employee
        fields = [
            "id",
            "email",
            "department",
            "status",
        ]


class CourseContentSerializer(serializers.ModelSerializer):
    content = ContentSerializer(read_only=True)

    class Meta:
        model = CourseContent
        exclude = [
            "id",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
            "course",
        ]


class CourseSerializer(serializers.ModelSerializer):
    course_contents = CourseContentSerializer(many=True, read_only=True)
    completion_rate = serializers.SerializerMethodField()
    course_progression = serializers.SerializerMethodField()
    is_started = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "description",
            "learning_type",
            "thumbnail",
            "material_count",
            "quiz_count",
            "questions_count",
            "duration",
            "course_contents",
            "completion_rate",
            "course_progression",
            "is_started",
            "is_completed",
        ]

    def get_completion_rate(self, obj) -> int:
        user = self.context["request"].user
        if user.role == Roles.EMPLOYEE:
            return None

        employees = Employee.objects.filter(emp_profile__organization=obj.organization)
        employees_courses = UserCourse.objects.filter(user__in=employees, course=obj)
        progress_rates = [
            employee_course.progress_rate for employee_course in employees_courses
        ]
        return (
            int(sum(progress_rates) / len(progress_rates) * 100)
            if progress_rates
            else 0
        )

    def get_course_progression(self, course) -> int:

        user = self.context["request"].user

        user_course = UserCourse.objects.filter(user=user, course=course).first()
        if not user_course:
            return 0
        else:
            return user_course.progress_rate

    def get_is_started(self, course) -> bool:
        user = self.context["request"].user
        user_course = UserCourse.objects.filter(user=user, course=course).first()
        if not user_course:
            return False
        else:
            return user_course.is_started

    def get_is_completed(self, course) -> bool:
        user = self.context["request"].user
        user_course = UserCourse.objects.filter(user=user, course=course).first()
        if not user_course:
            return False
        else:
            return user_course.is_completed
