import logging

from celery import shared_task

from campaign.models import Campaign
from users.models import Employee

logger = logging.getLogger(__name__)


@shared_task(name="Complete Learning Campaign Course")
def complete_course_campaign_course_task(
    employee_id: str, course_campaign_id: str, course_id: str
):
    campaign: Campaign = Campaign.objects.filter(
        course_campaign__id=course_campaign_id
    ).first()
    if not campaign:
        return
    course_campaign = campaign.course_campaign
    course = course_campaign.courses.filter(id=course_id).first()
    employee: Employee = course_campaign.employees.filter(id=employee_id).first()
    employee_course_campaign = employee.course_campaign_records.filter(
        course_campaign=course_campaign
    ).first()

    if not employee:
        return
    if not course:
        return
    if not employee_course_campaign:
        return

    course_campaign_course = course_campaign.campaign_courses.filter(
        course=course, employee=employee
    ).first()
    if course_campaign_course.progression_rate == 100:
        employee.complete_course_campaign_course(
            course=course,
            course_campaign=course_campaign,
            employee_course_campaign=employee_course_campaign,
        )


@shared_task(name="Course Campaigns Reminder Email")
def course_campaigns_reminder_email_task(campaign_id: str):
    from courses.models import CourseCampaign

    campaign: Campaign = Campaign.objects.filter(id=campaign_id).first()

    if not campaign:
        return

    course_campaign: CourseCampaign = campaign.course_campaign
    employees_records = course_campaign.employee_records.exclude(is_completed=True)
    for employee_record in employees_records:
        employee = employee_record.employee
        course_campaign.notify_employee_campaign_reminder(employee)
