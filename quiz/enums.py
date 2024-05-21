from django.db import models


class QuestionTypes(models.TextChoices):
    MULTICHOICE = "multichoice", "MultiChoice"
    SINGLECHOICE = "singlechoice", "SingleChoice"
