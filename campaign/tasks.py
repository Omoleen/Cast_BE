from celery import shared_task

from campaign.models import Campaign


@shared_task(name="Initiate Campaign")
def initiate_campaign_task(campaign_id: str):
    from campaign.models import Campaign

    campaign: Campaign = Campaign.objects.filter(id=campaign_id).first()
    if not campaign:
        return
    campaign.initiate_campaign()


@shared_task(name="Start Campaign")
def start_campaign(campaign_id: str):
    campaign: Campaign = Campaign.objects.filter(id=campaign_id).first()
    if not campaign:
        return
    if campaign.is_phishing_campaign:
        phishing_campaign = campaign.phishing_campaign
        phishing_campaign.start()
    elif campaign.is_course_campaign:
        course_campaign = campaign.course_campaign
        course_campaign.start()
