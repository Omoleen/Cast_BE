from rest_framework import serializers

from abstract.managers import SimpleModelManager
from abstract.toolboxes import PendulumToolbox
from quiz.models import Question, QuestionOption
from quiz.serializers import QuestionSerializer

from .models import CampaignContentSnapshot, Content


class ContentSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

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
            "has_questions",
            "duration",
        ]

    def get_is_completed(self, obj):
        user = self.context["request"].user
        return obj.completed_by.filter(id=user.id).exists()

    def get_duration(self, obj):
        return PendulumToolbox.convert_timedelta_to_duration(
            obj.duration, in_words=True
        )


class ContentDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

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
            "questions",
            "duration",
        ]


class ContentQuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = [
            "id",
            "text",
        ]


class ContentQuestionSerializer(serializers.ModelSerializer):
    options = ContentQuestionOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "type", "options"]
