import uuid
from datetime import timezone

from django.db import models

from abstract.utils import S3Client


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ["created_at"]

    def soft_delete(self):
        """soft  delete a model instance"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()


class BaseFile(BaseModel):
    name = models.CharField(("File name"), max_length=120, null=True, blank=True)
    path = models.URLField(("S3 Bucket url"), blank=True, null=True)
    size = models.FloatField(default=0)
    file_type = models.CharField(max_length=5, null=True, blank=True)
    file = models.FileField(upload_to="contents/", null=True, blank=True)

    is_uploaded = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def key(self):
        return self.path.split("amazonaws.com/")[1]

    def generate_presigned_url(self):
        s3 = S3Client()
        self.path = s3.get_presigned_url(self.id)
        self.save()
        return self.path

    # def save(self, *args, **kwargs):
    #     print("saving file")
    #     print(self.id, self.pk)
    #     if not self.id or self.pk is None:
    #         self.id = uuid.uuid4()
    #         print(self.id)
    #         # try:
    #         s3 = S3Client()
    #         self.path = s3.get_presigned_url(self.id)
    #     return super().save(*args, **kwargs)
