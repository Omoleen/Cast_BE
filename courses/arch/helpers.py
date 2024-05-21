from django.db.models import Q
from rest_framework import serializers

from abstract.managers import SimpleModelManager
from content.models.content import Content
from content.serializers import ContentSerializer
from users.models import Organization

from ..models import Course, CourseCampaign, CourseContent


class CourseContentHelper(SimpleModelManager):
    content_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True)
    contents = ContentSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = "__all__"
        extra_kwargs = {"content_ids": {"required": True}}

    def _validate_db(self, attrs):
        organization: Organization = self.context["request"].user
        content_objs = Content.objects.filter(
            Q(organization=organization) | Q(is_public=True)
        ).filter(id__in=attrs["content_ids"])
        existing_content_ids = set(content_obj.id for content_obj in content_objs)
        for content_id in attrs["content_ids"]:
            if content_id not in existing_content_ids:
                raise serializers.ValidationError(
                    "Content does not exist or you cannot add this content to your course"
                )
        self.content_objs = content_objs
        return attrs
