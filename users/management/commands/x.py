from django.conf import settings
from django.core.management import BaseCommand

from campaign.enums import CampaignStatus
from campaign.models import Campaign

# from library.models import Library
# from library.serializers import LibrarySerializer
from content.models import Content
from courses.models import CourseCampaign, EmployeeCourseCampaign
from phishing.models import PhishingCampaign, PhishingTemplate
from phishing.tasks import phishing_campaign_send_email_task
from users.models import Employee

# from quiz.models import Quiz
from ...models import AnsweredQuestion


class Command(BaseCommand):
    """Update all Trip Todos types"""

    def handle(self, *args, **kwargs):

        setattr(settings, "MANAGEMENT_SCRIPT", True)
        # employee = Employee.objects.first()
        # campaign = Campaign.objects.get(id="8235f327-ca14-4491-918a-70409218e7f2")
        # print(campaign.type)
        # print(campaign.phishing_campaign)
        # print(campaign.phishing_campaign.id)
        # phishing_campaign_send_email_task(employee.email, campaign.phishing_campaign.id)

        # Employee.objects.all().delete()
        # temp = PhishingTemplate.objects.filter(id="1a875289-a2f8-4904-85ca-8f78446a00d9").values("email_html_content")
        # print(temp)

        # camps: CourseCampaign = CourseCampaign.objects.all()
        # # for c in camp[]:
        # for camp in camps:
        #     camp.notify_employees_campaign_enrolled()
        # pprint(temp.landing_page_html_content)
        # libraries = Library.objects.first()

        # data = LibrarySerializer(libraries).data
        # pprint((data))
        # for i in range(4):
        #     print(uuid.uuid4())

        # AnsweredQuestion.objects.all().delete()
        # campaigns = Campaign.objects.all()
        # for campaign in campaigns:
        #     if campaign.status.lower() == "pending":
        #         campaign.status = CampaignStatus.SCHEDULED
        #         campaign.save()
        # for content in Content.objects.all():
        #     content.questions.all().delete()
        #     content.delete()
        #     print("delete:", content)
        setattr(settings, "MANAGEMENT_SCRIPT", False)

        self.stdout.write(self.style.SUCCESS("Done!"))
