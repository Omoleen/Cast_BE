from rest_framework import serializers

from .models import CampaignContentQuiz, Question, QuestionOption


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = [
            "id",
            "text",
            "is_correct",
        ]


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "type", "options"]


class CampaignContentQuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignContentQuiz
        fields = ["id", "questions"]
