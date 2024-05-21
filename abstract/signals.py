from django.db.models.signals import pre_save
from django.dispatch import receiver

from abstract.utils import S3Client

from .models import BaseFile

# @receiver(pre_save, sender=BaseFile)
# def generate_presigned_url(sender, instance=None, created=False, **kwargs) -> None:
#     if created:
#         print(instance.id)
#         s3 = S3Client()
#         instance.path = s3.get_presigned_url(instance.id)
