from functools import cached_property

from django.db import models
from django.utils.translation import gettext_lazy as _

from abstract.models import BaseModel
from users.models import Organization


class PhishingTemplate(BaseModel):
    organization = models.ForeignKey(
        Organization,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="phishing_templates",
    )
    name = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    vendor = models.CharField(max_length=256, null=True, blank=True)
    is_public = models.BooleanField(default=False)
    email_html_content = models.TextField(null=True, blank=True)
    email_css_styles = models.TextField(null=True, blank=True)
    email_subject = models.CharField(max_length=256, null=True, blank=True)
    email_sender = models.EmailField(null=True, blank=True)
    email_sender_name = models.CharField(max_length=256, null=True, blank=True)
    email_domain = models.CharField(max_length=256, null=True, blank=True)
    email_host = models.CharField(max_length=256, null=True, blank=True)
    email_port = models.IntegerField(null=True, blank=True)
    email_username = models.CharField(max_length=256, null=True, blank=True)
    email_password = models.CharField(max_length=256, null=True, blank=True)
    email_use_tls = models.BooleanField(default=False)
    email_use_ssl = models.BooleanField(default=False)
    landing_page_html_content = models.TextField(null=True, blank=True)
    landing_page_css_styles = models.TextField(null=True, blank=True)
    dynamic_context_keys = models.JSONField(
        _("Randomly generated fields during phishing campaign"),
        null=True,
        blank=True,
        default=list,
    )

    @cached_property
    def email_body(self):
        email_body = self.email_html_content
        email_body = email_body.replace(
            "</title>",
            f"""
            </title>
                <style>
                    {self.email_css_styles}
                </style>
        """,
        )
        return email_body

    def __str__(self):
        return self.name
