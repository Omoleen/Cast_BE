from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from courses.actions import update_course_thumbnails_duration

from .models import (
    AnsweredCourseCampaignQuestion,
    CompletedCourseCampaignContent,
    Course,
    CourseCampaign,
    CourseCampaignCourse,
    CourseContent,
    EmployeeCourseCampaign,
)

# Register your models here.

# admin.site.register(Course)
# admin.site.register(CourseContent)
admin.site.register(CourseCampaign)
admin.site.register(EmployeeCourseCampaign)
admin.site.register(CompletedCourseCampaignContent)
admin.site.register(AnsweredCourseCampaignQuestion)
admin.site.register(CourseCampaignCourse)


@admin.register(CourseContent)
class CourseContentAdmin(admin.ModelAdmin):
    model = CourseContent

    list_display = ["course", "content", "order"]
    ordering = ["course", "order"]
    list_filter = ["course", "content", "order"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    model = Course
    actions = [update_course_thumbnails_duration]
    list_display = [
        "id",
        "name",
        "thumbnail",
        "organization",
        "is_public",
        "learning_type",
    ]
    list_filter = ["name", "is_public", "learning_type"]
    fieldsets = [
        [
            None,
            {
                "fields": [
                    "name",
                    "description",
                    "organization",
                    "is_public",
                    "learning_type",
                    "thumbnail",
                ]
            },
        ]
    ]
    search_fields = [
        "name",
    ]

    def get_readonly_fields(
        self, request: HttpRequest, obj: Any | None = ...
    ) -> list[str] | tuple[Any, ...]:
        if obj:
            return []
        else:
            return []
