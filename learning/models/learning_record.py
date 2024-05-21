from django.db import models

from abstract.models import BaseModel
from content.models import Content
from users.models import Employee


class LearningRecord(BaseModel):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="learning_records"
    )
    content = models.ForeignKey(
        Content, on_delete=models.SET_NULL, null=True, related_name="records"
    )
    is_completed = models.BooleanField(default=False)
