from functools import cached_property

from django.core.files import File
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from abstract.models import BaseFile, BaseModel
from campaign.enums import CampaignTypes
from Castellum.enums import LearningTypes
from users.models import Organization

from ..enums import ContentTypes


class Content(BaseFile):
    title = models.CharField(max_length=512)
    description = models.TextField(null=True, blank=True)
    type = models.CharField(
        max_length=256, choices=ContentTypes.choices, null=True, blank=True
    )
    learning_type = models.CharField(
        max_length=256, choices=LearningTypes.choices, null=True, blank=True
    )
    instructor_name = models.CharField(max_length=256, null=True, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="content",
    )
    is_public = models.BooleanField(default=False)
    duration = models.DurationField(null=True, blank=True)
    thumbnail = models.ImageField(
        upload_to="thumbnails/courses/", null=True, blank=True
    )

    def __str__(self):
        return self.title

    # def thumbnail_tag(self):
    #     return f'<img src="{self.thumbnail.url}" width="150" height="150" />'

    # thumbnail_tag.short_description = "Thumbnail"

    def save(self, *args, **kwargs):
        # from content.tasks import update_duration_thumbnail
        file: File = self.file
        if file:
            self.name = file.name
            self.size = file.size / 1000000
            self.file_type = "." + file.name.split(".")[-1]
            self.is_uploaded = True
            self.uploaded_at = timezone.now()
            # self.path = file.path

        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.file.delete()
        return super().delete(*args, **kwargs)

    def get_score(self, user):
        answered_questions = user.answered_questions.filter(
            question__in=self.questions.all()
        )
        score = 0
        for answered_question in answered_questions:
            if answered_question.is_correct:
                score += 1
        return score

    def get_campaign_score(self, user):
        answered_questions = user.answered_campaign_questions.filter(
            question__in=self.questions.all()
        )
        score = 0
        for answered_question in answered_questions:
            if answered_question.is_correct:
                score += 1
        return score

    @cached_property
    def has_questions(self):
        return self.questions.exists()
