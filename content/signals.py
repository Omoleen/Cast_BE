from django.core.files import File
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django_mailbox.models import Message

# from abstract.toolboxes.thumbnail import ThumbnailGenerator
from users.enums import ActivityType
from users.models import ActivityLog, Employee, User

from .models import Content

# from moviepy.video.io.VideoFileClip import VidxeoFileClip


@receiver(post_save, sender=Content)
def update_duration_thumbnail(sender, instance: Content, created, **kwargs) -> None:
    # if created:
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
