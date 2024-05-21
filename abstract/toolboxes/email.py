from abc import ABC, abstractmethod
from functools import cached_property

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from ..tasks import send_email


class Email(ABC):
    @abstractmethod
    def __init__(self, user) -> None:
        self.user = user

    @abstractmethod
    def context(self):
        ...

    @abstractmethod
    def subject(self):
        ...

    @abstractmethod
    def html_body(self):
        ...

    def from_email(self):
        return settings.DEFAULT_FROM_EMAIL

    @cached_property
    def to_email(self):
        ...


class OrganizationActivationEmail(Email):
    def __init__(self, organization):
        self.organization = organization

    @cached_property
    def context(self):
        token = self.organization.set_token()
        return {
            "name": self.organization.org_profile.name.title(),
            "activation_link": f"{settings.FRONTEND_URL}account-activation/{token}",
            "tracking_id": "81067dbe-c269-4c5d-8388-31dee27c93e2",
        }

    @cached_property
    def subject(self):
        return "Activate Your Account"

    @cached_property
    def html_body(self):
        context = self.context
        return render_to_string("emails/users/account_activation.html", context)
        # return f"Your Activation link is {context['activation_link']}"

    @cached_property
    def to_email(self):
        return [self.organization.email]


class PasswordResetEmail(Email):
    def __init__(self, user):
        self.user = user

    @cached_property
    def context(self):
        from users.models import Employee, Organization, User

        token = self.user.set_token()
        user: User = self.user
        if user.is_organization:
            user.__class__ = Organization
            name = user.org_profile.name.title()
        else:
            user.__class__ = Employee
            name = user.emp_profile.first_name.title()

        return {
            "name": name,
            "password_reset_link": f"{settings.FRONTEND_URL}password-reset/{token}",
        }

    @cached_property
    def subject(self):
        return "Reset Your Account Password"

    @cached_property
    def html_body(self):
        context = self.context
        return render_to_string("emails/users/password_reset.html", context)
        # return f"Your Password Reset link is {context['password_reset_link']}"

    @cached_property
    def to_email(self):
        return [self.user.email]


class PasswordChangedEmail(Email):
    def __init__(self, user):
        self.user = user

    @cached_property
    def context(self):
        from users.models import Employee, Organization, User

        user: User = self.user
        if user.is_organization:
            user.__class__ = Organization
            name = user.org_profile.name.title()
        else:
            user.__class__ = Employee
            name = user.emp_profile.first_name.title()
        return {
            "name": name,
        }

    @cached_property
    def subject(self):
        return "Password Change Successful"

    @cached_property
    def html_body(self):
        context = self.context
        return render_to_string("emails/users/password_changed.html", context)
        # return f"Your password has been changed successfully"

    @cached_property
    def to_email(self):
        return [self.user.email]


class EmployeeInviteEmail(Email):
    def __init__(self, employee):
        self.employee = employee

    @cached_property
    def context(self):
        token = self.employee.set_token()
        profile = self.employee.emp_profile
        return {
            "name": profile.first_name.title(),
            "organization": profile.organization.org_profile.name.title(),
            "invite_link": f"{settings.FRONTEND_URL}employee-invite/{token}",
        }

    @cached_property
    def subject(self):
        return "You have been invited to join Castellum"

    @cached_property
    def html_body(self):
        context = self.context
        return render_to_string("emails/users/employee_invite.html", context)
        # return f"Your Invite link is {context['invite_link']}"

    @cached_property
    def to_email(self):
        return [self.employee.email]


class UserEmailToolbox:
    def __init__(self, user, action):
        self.user = user
        self.action = action

    def actions_to_email(self):
        actions_dict = {
            "organization-activation": OrganizationActivationEmail,
            "employee-invite": EmployeeInviteEmail,
            "password-reset": PasswordResetEmail,
            "password-changed": PasswordChangedEmail,
        }
        return actions_dict.get(self.action)(self.user)

    def send_email(
        self,
    ):
        email_instance = self.actions_to_email()
        send_email.delay(
            email_subject=email_instance.subject,
            email_body=email_instance.html_body,
            to_email=email_instance.to_email,
        )
