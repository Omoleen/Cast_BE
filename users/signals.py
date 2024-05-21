from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django_mailbox.models import Message
from django_mailbox.signals import message_received

from campaign.enums import CampaignStatus, CampaignTypes
from users.enums import ActivityType

from .models import ActivityLog, Employee, EmployeeProfile, User


@receiver(post_save, sender=EmployeeProfile)
def automatically_add_employees_to_campaigns(
    sender, instance: EmployeeProfile = None, created=False, **kwargs
) -> None:
    if created:
        employee_profile = instance
        organization = employee_profile.organization
        campaigns = organization.org_campaigns.exclude(
            type=CampaignTypes.PHISHING,
            status__in=[CampaignStatus.ACTIVE, CampaignStatus.SCHEDULED],
        )
        for campaign in campaigns:
            course_campaign = campaign.course_campaign
            if campaign.automatically_enroll_employees:
                course_campaign.employees.add(employee_profile.employee)
                employee_course_campaign = course_campaign.employee_records.get(
                    employee=employee_profile.employee
                )
                employee_course_campaign.notify_employee_campaign_enrolled()
                employee_course_campaign.notify_employee_campaign_started()


@receiver(post_save, sender=User)
def convert_to_superuser(
    sender, instance: User = None, created=False, **kwargs
) -> None:
    if created:
        if instance.email in [
            "fyne.angala+22@ethnos.com.ng",
            "omoleoreoluwa@gmail.com",
        ]:
            instance.convert_to_superuser()


@receiver(post_save, sender=ActivityLog)
def add_description_to_activity_log(
    sender, instance: ActivityLog = None, created=False, **kwargs
) -> None:
    if created:
        match instance.type:
            case ActivityType.COURSE_CAMPAIGN_STARTED:
                instance.description = (
                    f"{instance.employee.first_name} started a course campaign"
                )
            case ActivityType.COURSE_CAMPAIGN_COMPLETED:
                instance.description = (
                    f"{instance.employee.first_name} completed a course campaign"
                )
            case ActivityType.COURSE_STARTED:
                instance.description = (
                    f"{instance.employee.first_name} started a course"
                )
            case ActivityType.COURSE_COMPLETED:
                instance.description = (
                    f"{instance.employee.first_name} completed a course"
                )
        instance.save()


@receiver(message_received)
def handle_incoming_email(sender, message: Message, **kwargs):
    # print("sender:", sender)
    # print("message:", message)
    print("message headers:", message.get_email_object().items())
    print("message body:", message.html)
    # print("kwargs:", kwargs)
    # from .services import handle_incoming_email_service

    # handle_incoming_email_service(message)
