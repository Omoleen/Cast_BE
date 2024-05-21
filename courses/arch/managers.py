from django.db import models
from django.db.models import Q
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from abstract.managers import SimpleModelManager
from content.models.content import Content
from content.serializers import ContentSerializer
from users.models import AnsweredQuestion, Organization, User, UserCourse

from ..models import Course, CourseCampaign, CourseContent
from ..serializers import (
    CourseCampaignSerializer,
    CourseContentSerializer,
    CourseSerializer,
)
from .helpers import CourseContentHelper


class CreateCourseManager(SimpleModelManager):
    class Meta:
        model = Course
        fields = "__all__"
        extra_kwargs = {
            "name": {"required": True},
            "organization": {"read_only": True},
        }

    def _validate_db(self, attrs):
        if self.Meta.model.objects.filter(name=attrs["name"]).exists():
            raise serializers.ValidationError("Course name already exists")
        return attrs

    def _create(self, validated_data):
        organization = self.context["request"].user
        course = self.Meta.model.objects.create(
            organization=organization, **validated_data
        )
        return course


class AddContentManager(CourseContentHelper):
    def _update(self, instance, validated_data):
        course: Course = instance
        content_objs = self.content_objs
        course.contents.add(*content_objs)
        return course


class RemoveContentSerializer(CourseContentHelper):
    def _update(self, instance, validated_data):
        course: Course = instance
        content_objs = self.content_objs
        course.contents.remove(*content_objs)
        return course


class CompleteCourseManager(SimpleModelManager):
    score = serializers.IntegerField(read_only=True)
    question_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = ["id", "score", "question_count"]
        extra_kwargs = {"id": {"required": True}}

    def _validate_db(self, attrs):
        course: Course = self.instance
        user: User = self.context["request"].user
        course_contents = course.contents.all()
        incompleted_contents = course_contents.exclude(completed_by=user)
        user_course = UserCourse.objects.filter(user=user, course=course).first()

        if incompleted_contents.exists():
            raise serializers.ValidationError(
                "Complete all contents to complete the course"
            )
        if not user_course:
            raise serializers.ValidationError(
                "You have to start the course before completing it"
            )

        self.user_course = user_course
        return attrs

    def _update(self, instance, validated_data):
        course: Course = instance
        # user: User = self.context["request"].user
        user_course: UserCourse = self.user_course
        user_course.mark_as_completed()

        # generate score
        self.user_course_score = user_course.score

        return course

    def _to_representation(self, instance):
        return {
            "score": self.user_course_score,
            "question_count": instance.questions_count,
        }


class StartCourseManager(SimpleModelManager):
    class Meta:
        model = Course
        fields = ["id"]
        extra_kwargs = {"id": {"required": True}}

    def _update(self, instance, validated_data):
        course: Course = instance
        user: User = self.context["request"].user
        user.start_course(course)
        return course


class RetakeCourseManager(SimpleModelManager):
    class Meta:
        model = Course
        fields = ["id"]
        extra_kwargs = {"id": {"required": True}}

    def _update(self, instance, validated_data):
        course: Course = instance
        user: User = self.context["request"].user
        user_course = UserCourse.objects.filter(
            user=user,
            course=course,
        ).first()
        if not user_course:
            raise serializers.ValidationError(
                "You have not started/completed this course"
            )
        user_course.retake()
        return course


class AnsweredQuestionSerializer(ModelSerializer):
    question = serializers.JSONField(source="question_options_snapshot")
    selected_answers = serializers.JSONField(source="answers_snapshot")

    class Meta:
        model = AnsweredQuestion
        fields = ["question", "selected_answers"]


class PersonalCoursePerformanceManager(SimpleModelManager):
    class Meta:
        model = Course
        fields = ["id"]
        extra_kwargs = {"id": {"required": True}}

    def validate(self, attrs):

        return attrs

    def _to_representation(self, instance):
        course: Course = instance
        user: User = self.context["request"].user
        user_course = UserCourse.objects.filter(user=user, course=course).first()
        if not user_course or not user_course.is_completed:
            raise serializers.ValidationError(
                "You have not attempted/completed this course"
            )

        answered_questions = AnsweredQuestion.objects.filter(
            user=user, content__in=instance.contents.all(), course=instance
        )
        return AnsweredQuestionSerializer(answered_questions, many=True).data
