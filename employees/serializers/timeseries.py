from rest_framework import serializers

from users.models import UserTimeSeriesCompletedCourses, UserTimeSeriesSecurityScore


class UserTimeSeriesSecurityScoreSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(source="created_at")

    class Meta:
        model = UserTimeSeriesSecurityScore
        fields = ["date", "security_score"]


class UserTimeSeriesCompletedCoursesSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(source="created_at")

    class Meta:
        model = UserTimeSeriesCompletedCourses
        fields = ["date", "courses_completed"]
