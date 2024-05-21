# from . import CampaignQuiz
from django.db import models

from abstract.models import BaseModel
from campaign.models import Campaign
from users.models import Employee

# class CampaignQuizRecord(BaseModel):
#     """
#     questions: [
#         {
#             question: "Who is the king of the jungle?",
#             available_options: [{
#                 "option": "Tiger",
#                 "answer": True
#             },
#             {
#                 "option": "Lion",
#                 "answer": False
#             }],
#             answer: "Lion"
#         }
#     ]
#     """
#     employee = models.OneToOneField(Employee,
#                                     on_delete=models.CASCADE,
#                                     related_name="quiz_records")
#     campaign = models.ForeignKey(Campaign,
#                                  on_delete=models.CASCADE,
#                                  related_name="quiz_records")
#     campaign_quiz = models.ForeignKey(CampaignQuiz,
#                                       on_delete=models.CASCADE,
#                                       related_name="records")
#     answered_questions = models.JSONField()
#     date_taken = models.DateTimeField(null=True)
#     duration = models.FloatField(null=True, blank=True)
#     start_time = models.TimeField(null=True, blank=True)
#     end_time = models.TimeField(null=True, blank=True)
