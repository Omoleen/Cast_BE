from django.contrib import admin

from .models import Campaign


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    model = Campaign
    list_display = [
        "name",
        "organization",
        "type",
        "start_date",
        "end_date",
        "status",
        "last_step_completed",
        "created_at",
    ]
    list_filter = [
        "type",
        "status",
        "start_date",
        "end_date",
        "last_step_completed",
        "organization",
    ]
    fieldsets = [
        [
            None,
            {
                "fields": [
                    "organization",
                    "name",
                    "description",
                    "type",
                    "status",
                    "start_date",
                    "end_date",
                    "last_step_completed",
                    "automatically_enroll_employees",
                    "background_task_ids",
                ]
            },
        ]
    ]

    add_fieldsets = [
        [
            None,
            {
                "fields": [
                    "organization",
                    "name",
                    "description",
                    "type",
                    "status",
                    "start_date",
                    "end_date",
                    "last_step_completed",
                    "automatically_enroll_employees",
                    "background_task_ids",
                ]
            },
        ]
    ]

    search_fields = [
        "name",
        "description",
        "organization",
    ]
