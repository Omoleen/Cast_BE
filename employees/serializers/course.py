from rest_framework import serializers

from courses.models import Course


class LearningResourceCourseSerializer(serializers.ModelSerializer):
    button_text = serializers.SerializerMethodField()
    course_card_type = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ["name", "thumbnail", "duration", "button_text", "course_card_type"]

    def get_button_text(self, obj):
        return self.context.get("button_text")

    def get_course_card_type(self, obj):
        return self.context.get("course_card_type")
