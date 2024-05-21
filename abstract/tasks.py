from email.mime.image import MIMEImage

from celery import shared_task
from django.core.mail import EmailMessage, EmailMultiAlternatives


@shared_task(name="Task to send Emails")
def send_email(email_subject, email_body, to_email, headers=None):
    msg = EmailMessage(
        subject=email_subject,
        body=email_body,
        to=to_email if isinstance(to_email, list) else [to_email],
        headers=headers,
    )
    msg.content_subtype = "html"
    msg.send()


@shared_task(name="Background update model field")
def update_model_field(model_name, id, field, value):
    from users.models import AuthorizedDomain, DeliverabilityTest, User

    match model_name:
        case "AuthorizedDomain":
            model = AuthorizedDomain
        case "User":
            model = User
        case "DeliverabilityTest":
            model = DeliverabilityTest
        case _:
            return None

    instance = model.objects.filter(id=id).first()
    if not instance:
        return None
    setattr(instance, field, value)
    instance.save()
