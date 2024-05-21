from django.db import models
from rest_framework import serializers

from abstract.managers import SimpleModelManager
from courses.models import Course
from quiz.enums import QuestionTypes
from quiz.models import Question, QuestionOption
from quiz.serializers import QuestionOptionSerializer, QuestionSerializer
from users.models import AnsweredQuestion, CompletedContent, User, UserCourse

from ..models import CampaignContentSnapshot, Content
from ..serializers import (
    ContentDetailSerializer,
    ContentQuestionOptionSerializer,
    ContentQuestionSerializer,
    ContentSerializer,
)
from ..tasks import update_completed_content


class InitiateContentCreationManager(SimpleModelManager):
    # upload_url = serializers.URLField(read_only=True)
    class Meta:
        model = Content
        fields = [
            "title",
            "description",
            "type",
            "learning_type",
            "is_public",
            "path",
            "is_uploaded"
            # "upload_url"
        ]
        extra_kwargs = {"path": {"read_only": True}, "is_uploaded": {"read_only": True}}

    def _validate_db(self, attrs):
        organization = self.context["request"].user
        existing_content = Content.objects.filter(
            title=attrs["title"], organization=organization
        ).exists()
        if existing_content:
            raise serializers.ValidationError("Content with this title already exists")
        return attrs

    def _create(self, validated_data):
        organization = self.context["request"].user
        validated_data["organization"] = organization
        content: Content = Content.objects.create(**validated_data)
        content.generate_presigned_url()
        return content


class ContentDetailManager(SimpleModelManager):
    is_completed = serializers.SerializerMethodField()
    questions = ContentQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Content
        fields = [
            "id",
            "title",
            "description",
            "type",
            "path",
            "thumbnail",
            "learning_type",
            "is_completed",
            "questions",
        ]

    def get_is_completed(self, obj):
        user = self.context["request"].user
        return obj.completed_by.filter(id=user.id).exists()


class CompleteContentManager(SimpleModelManager):
    class Meta:
        model = Content
        fields = ["id"]
        extra_kwargs = {"id": {"required": True}}

    def _validate_db(self, attrs):
        content: Content = self.instance
        course: Course = self.context["course"]
        user: User = self.context["request"].user
        user_course: UserCourse = UserCourse.objects.filter(
            user=user, course=course
        ).first()
        if content.has_questions:
            raise serializers.ValidationError(
                "This endpoint only works for contents without questions"
            )
        if not user_course:
            raise serializers.ValidationError(
                "You have to start the course before completing contents"
            )
        self.user_course = user_course
        return attrs

    def _update(self, instance, validated_data):
        user: User = self.context["request"].user
        course: Course = self.context["course"]
        user_course: UserCourse = self.user_course
        user.complete_content(instance, course, user_course)
        return instance

    def _to_representation(self, instance):
        return "Content completed successfully"


class AnswerQuestionManager(SimpleModelManager):
    question_id = serializers.CharField(write_only=True)
    answer_ids = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=True
    )
    course_id = serializers.CharField(write_only=True)

    class Meta:
        model = Content
        fields = ["question_id", "answer_ids", "course_id"]

    def _validate_db(self, attrs):
        question = Question.objects.filter(id=attrs["question_id"]).first()
        if not question:
            raise serializers.ValidationError("Question not found")
        answers = QuestionOption.objects.filter(id__in=attrs["answer_ids"])
        if not answers.exists():
            raise serializers.ValidationError("Answer not found")

        content_question = self.instance.questions.filter(id=question.id).first()
        if not content_question:
            raise serializers.ValidationError("Question not found in content")
        if content_question.type == QuestionTypes.SINGLECHOICE and len(answers) > 1:
            raise serializers.ValidationError("Single choice question")
        elif (
            content_question.type == QuestionTypes.MULTICHOICE
            and len(answers) > content_question.options.count()
        ):
            raise serializers.ValidationError(
                "answers are morve than the available options"
            )
        question_answers = question.options.filter(
            id__in=answers.values_list("id", flat=True)
        )
        if not question_answers.exists():
            raise serializers.ValidationError("Answer not found in question")
        course = Course.objects.filter(id=attrs["course_id"]).first()
        if not course:
            raise serializers.ValidationError("Course not found")
        self.question = question
        self.answers = answers
        self.course = course
        return super()._validate_db(attrs)

    def _update(self, instance, validated_data):
        user: User = self.context["request"].user
        content = instance
        question: Question = self.question
        answers: models.QuerySet[QuestionOption] = self.answers
        course: Course = self.course
        answered_question, _ = AnsweredQuestion.objects.update_or_create(
            user=user,
            question=question,
            content=content,
            course=course,
            defaults={
                "question_options_snapshot": ContentQuestionSerializer(question).data,
                "answers_snapshot": QuestionOptionSerializer(answers, many=True).data,
            },
        )
        answered_question.answers.set(answers)
        self.user = user
        self.content = content
        return instance

    def _misc(self, data):
        user: User = self.user
        content: Content = self.content
        course: Course = self.course
        update_completed_content.delay(user.id, content.id, course.id)
        return

    def _to_representation(self, instance):
        return "Answer submitted successfully"


class AnswerCourseContentQuestionManager(SimpleModelManager):
    answer_ids = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=True
    )

    class Meta:
        model = Question
        fields = ["answer_ids"]

    def _validate_db(self, attrs):
        course = attrs["course"] = self.context["course"]
        question = attrs["question"] = self.context["question"]
        content = attrs["content"] = self.context["content"]
        user_course: UserCourse = UserCourse.objects.filter(
            user=self.context["request"].user, course=course
        ).first()
        answers = QuestionOption.objects.filter(
            id__in=attrs["answer_ids"], question=question
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

        if not user_course:
            raise serializers.ValidationError(
                "You have to start the course before answering questions"
            )

        self.question = question
        self.answers = answers
        self.course = course
        self.content = content
        self.user_course = user_course
        return super()._validate_db(attrs)

    def _update(self, instance, validated_data):
        user: User = self.context["request"].user
        content: Content = self.content
        question: Question = self.question
        answers: models.QuerySet[QuestionOption] = self.answers
        course: Course = self.course
        user_course: UserCourse = self.user_course

        user.answer_course_content_question(
            content, question, answers, course, user_course
        )

        self.user = user
        self.content = content
        return instance

    # def _misc(self, data):
    #     user: User = self.user
    #     content: Content = self.content
    #     course: Course = self.course
    # update_completed_content.delay(user.id, content.id, course.id)
    #     return

    def _to_representation(self, instance):
        return "Answer submitted successfully"
