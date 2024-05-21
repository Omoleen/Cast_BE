from django.contrib import admin
from django.core.files import File

# from moviepy.video.io.VideoFileClip import VideoFileClip

# from abstract.toolboxes.thumbnail import ThumbnailGenerator


@admin.action(description="Generate Thumbnails/Update Duration for selected contents")
def update_content_thumbnails_duration(modeladmin, request, queryset):
    # for instance in queryset:
    #     instance.duration = timedelta(
    #         seconds=VideoFileClip(instance.file.path).duration
    #     )
    #     thumbnail_name = (
    #         f"thumbnail-{instance.file.name.replace(instance.file_type, '.jpg')}"
    #     )
    #     instance.thumbnail.save(
    #         name=thumbnail_name,
    #         content=File(
    #             ThumbnailGenerator().generate_thumbnail(file_path=instance.file.path)
    #         ),
    #         save=False,
    #     )
    #     instance.save()
    ...
