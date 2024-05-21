from datetime import timedelta
from functools import cached_property

from django.db import models

from abstract.models import BaseModel
from abstract.toolboxes import PendulumToolbox
from Castellum.enums import LearningTypes
from users.models import Organization


class Course(BaseModel):
    name = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
    )
    is_public = models.BooleanField(default=False)
    contents = models.ManyToManyField(
        "content.Content",
        related_name="courses",
        blank=True,
        through="CourseContent",
    )
    learning_type = models.CharField(
        max_length=256, choices=LearningTypes.choices, default=LearningTypes.GENERAL
    )
    # thumbnail = models.URLField(null=True, blank=True)
    thumbnail = models.ImageField(
        upload_to="thumbnails/contents/", null=True, blank=True
    )

    def __str__(self):
        return self.name

    # def thumbnail_tag(self):
    #     return f'<img src="{self.thumbnail.url}" width="150" height="150" />'

    # thumbnail_tag.short_description = "Thumbnail"

    # def save()

    @cached_property
    def material_count(self):
        return self.contents.count()

    @cached_property
    def quiz_count(self):
        count = 0
        contents = self.contents.prefetch_related("questions").all()
        for content in contents:
            if content.questions.exists():
                count += 1
        return count

    @cached_property
    def questions_count(self):
        count = 0
        contents = self.contents.prefetch_related("questions").all()
        for content in contents:
            count += content.questions.count()
        return count

    @cached_property
    def duration(self):
        duration = sum(
            [
                duration
                for duration in self.contents.all().values_list("duration", flat=True)
                if duration
            ],
            timedelta(seconds=0),
        )

        return PendulumToolbox.convert_timedelta_to_duration(duration, in_words=True)

    @cached_property
    def duration_in_timedelta(self):
        duration = sum(
            [
                duration
                for duration in self.contents.all().values_list("duration", flat=True)
                if duration
            ],
            timedelta(seconds=0),
        )

        return PendulumToolbox.convert_timedelta_to_duration(duration)

    def get_score(self, user):
        score = 0
        for content in self.contents.all():
            score += content.get_score(user)
        return score


class CourseContent(BaseModel):
    course = models.ForeignKey(
        "Course", on_delete=models.CASCADE, related_name="course_contents"
    )
    content = models.ForeignKey(
        "content.Content", on_delete=models.CASCADE, related_name="course_contents"
    )
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.name} - {self.content.title} - {self.order}"
