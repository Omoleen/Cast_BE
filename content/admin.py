from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from .actions.content import update_content_thumbnails_duration
from .models import CampaignContentSnapshot, Content

# Register your models here.

# admin.site.register(Content)
admin.site.register(CampaignContentSnapshot)


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    model = Content
    actions = [update_content_thumbnails_duration]
    list_display = [
        "id",
        "title",
        "thumbnail",
        "learning_type",
        "instructor_name",
        "is_public",
        "is_uploaded",
    ]
    list_filter = ["title", "learning_type", "is_public", "duration"]
    fieldsets = [
        [
            None,
            {
                "fields": [
                    "thumbnail",
                    "name",
                    "path",
                    "size",
                    "file_type",
                    "is_uploaded",
                    "uploaded_at",
                    "title",
                    "description",
                    "learning_type",
                    "instructor_name",
                    "organization",
                    "is_public",
                    "file",
                    "duration",
                ]
            },
        ]
    ]
    add_fieldsets = [
        [
            None,
            {
                "fields": [
                    "title",
                    "description",
                    "learning_type",
                    "instructor_name",
                    "organization",
                    "is_public",
                    "file",
                ],
                "classes": ("wide",),
            },
        ]
    ]
    search_fields = [
        "name",
        "title",
    ]

    def get_readonly_fields(
        self, request: HttpRequest, obj: Any | None = ...
    ) -> list[str] | tuple[Any, ...]:
        if obj:
            return [
                "id",
                "thumbnail",
                "name",
                "path",
                "size",
                "file_type",
                "is_uploaded",
                "uploaded_at",
                "duration",
            ]
        else:
            return []


# admin.site.register(Content, ContentAdmin)
