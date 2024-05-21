from django.contrib import admin
from django.core.files import File
from django.db.models import QuerySet

# from abstract.toolboxes.thumbnail import ThumbnailGenerator
from content.models import Content
from courses.models import Course

# from moviepy.video.io.VideoFileClip import VideoFileClip


@admin.action(description="Generate Thumbnails/Update Duration for selected Courses")
def update_course_thumbnails_duration(modeladmin, request, queryset: QuerySet[Course]):
    # for course in queryset:
    #     duration = timedelta(seconds=0)
    #     content_thumbnails = course.contents.filter(thumbnail__isnull=False)
    #     content_thumbnail: Content = random.choice(content_thumbnails)
    #     for content in course.contents.all():
    #         if content.duration:
    #             duration += content.duration
    #     thumbnail_name = f"thumbnail-{course.name.replace(' ', '_')}.jpg"
    #     course.thumbnail.save(
    #         name=thumbnail_name, content=content_thumbnail.thumbnail.file, save=False
    #     )
    #     course.duration = duration
    #     course.save()
    ...
