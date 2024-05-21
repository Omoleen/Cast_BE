# from campaign.models import Campaign
# from content.models import CampaignContentSnapshot
from django.db import models

from abstract.models import BaseModel

# class CampaignQuiz(BaseModel):
#     """
#     questions: [
#         {
#             id: 223223RRE2RREWEREW
#             question: "Who is the king of the jungle?",
#             available_options: [{
#                 "option": "Tiger",
#                 "answer": True
#             },
#             {
#                 "option": "Lion",
#                 "answer": False
#             }]
#         }
#     ]
#     """
#     campaign = models.ForeignKey(Campaign,
#                                  related_name="campaign_questions",
#                                  on_delete=models.CASCADE)
#     questions = models.JSONField()
#     deadline = models.DateTimeField(null=True)


class CampaignContentQuiz(BaseModel):
    """
    questions: [
        {
            id: 223223RRE2RREWEREW
            question: "Who is the king of the jungle?",
            available_options: [{
                "option": "Tiger",
                "answer": True
            },
            {
                "option": "Lion",
                "answer": False
            }]
        }
    ]
    """

    content = models.ForeignKey(
        "content.CampaignContentSnapshot",
        related_name="content_questions",
        on_delete=models.CASCADE,
    )
    questions = models.JSONField(default=list)
    deadline = models.DateTimeField(null=True, blank=True)
