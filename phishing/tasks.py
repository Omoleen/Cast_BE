import factory
import factory.fuzzy
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import get_connection
from django.core.mail.message import EmailMessage, EmailMultiAlternatives
from django.template import Context, Template
from django.template.loader import render_to_string
from django.utils import timezone
from faker import Faker

from abstract.tasks import send_email
from campaign.models import Campaign
from phishing.enums import PhishingActions
from users.models import Organization
from users.services import UserImport

User = get_user_model()


def send_phishing_email(
    email_headers,
    email_subject,
    to_email,
    from_email,
    html_body,
    email_host,
    email_port,
    email_username,
    email_password,
    email_use_tls,
    email_use_ssl,
):

    with get_connection(
        host=email_host,
        port=email_port,
        username=email_username,
        password=email_password,
        use_tls=email_use_tls,
        use_ssl=email_use_ssl,
    ) as connection:
        for email in to_email:

            msg = EmailMessage(
                subject=email_subject,
                body=html_body,
                to=[email],
                from_email=from_email,
                connection=connection,
                headers=email_headers,
            )
            msg.content_subtype = "html"
            # msg.attach_alternative(email_body, "text/html")
            msg.send()


@shared_task(
    name="Send email to an employee for phishing campaign",
    max_retries=5,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def phishing_campaign_send_email_task(employee_email: str, phishing_campaign_id: str):
    from .models import EmployeePhishingCampaign, PhishingCampaign, PhishingTemplate

    phishing_campaign: PhishingCampaign = PhishingCampaign.objects.filter(
        id=phishing_campaign_id
    ).first()
    employee_phishing_campaign: EmployeePhishingCampaign = (
        phishing_campaign.employee_records.filter(
            employee__email=employee_email
        ).first()
    )

    phishing: PhishingTemplate = employee_phishing_campaign.get_phishing()
    template = Template(phishing.email_body)
    from_email = phishing.email_sender

    context = {}
    dynamic_context_keys = phishing.dynamic_context_keys
    fake = Faker()
    name = fake.name()
    for key in dynamic_context_keys:
        match key:
            case "email_sender_name":
                from_email = f"{name} <{phishing.email_sender}>"
            case "name":
                context[key] = name
            case _:

                ...
    html_content = template.render(Context(context))

    data = {
        "email_headers": {
            settings.PHISHING_EMAIL_HEADERS[0]: employee_phishing_campaign.id,
        },
        "html_body": html_content,
        "to_email": [employee_email],
        "email_subject": phishing.email_subject,
        "from_email": from_email,
        "email_host": phishing.email_host,
        "email_port": phishing.email_port,
        "email_username": phishing.email_username,
        "email_password": phishing.email_password,
        "email_use_tls": phishing.email_use_tls,
        "email_use_ssl": phishing.email_use_ssl,
    }
    send_phishing_email(**data)
    employee_phishing_campaign.email_sent()
