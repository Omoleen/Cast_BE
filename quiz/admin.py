from django.contrib import admin

from .models import CampaignContentQuiz, Question, QuestionOption

# Register your models here.

admin.site.register(Question)
admin.site.register(CampaignContentQuiz)
admin.site.register(QuestionOption)
