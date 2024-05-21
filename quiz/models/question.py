from functools import cached_property

from django.db import models

from abstract.models import BaseModel
from content.models import Content
from users.models import Organization

from ..enums import QuestionTypes


class Question(BaseModel):
    content = models.ForeignKey(
        Content, on_delete=models.CASCADE, related_name="questions", null=True
    )
    organization = models.ForeignKey(
        Organization,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="quiz_questions",
    )
    text = models.TextField()
    type = models.CharField(
        max_length=256,
        choices=QuestionTypes.choices,
        default=QuestionTypes.SINGLECHOICE,
    )
    is_public = models.BooleanField(default=False)

    @cached_property
    def get_correct_answers(self):
        return self.options.filter(is_correct=True).values_list("text", flat=True)


class QuestionOption(BaseModel):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="options"
    )
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.question} - {self.text}"

    @cached_property
    def get_correct_answers(self):
        return self.question.options.filter(is_correct=True).values_list(
            "answer", flat=True
        )

    @cached_property
    def question_text(self):
        return self.question.text
