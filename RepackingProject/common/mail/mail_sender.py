import logging

from django.conf import settings
from django.template.loader import render_to_string

from CeleryApp.tasks import send_mail_use_broker_task


class SenderEmail:
    template = None
    context = None
    subject = None
    email_addresses = None

    def __init__(self, email, context):
        self.context = context
        self.email_addresses = email

    def send(self, filename=None):
        self.context["website_name"] = settings.WEBSITE_NAME
        self.context["schema"] = settings.SCHEMA
        self.context["domain"] = settings.DOMAIN
        self.context["port"] = settings.PORT
        self.context["support_email"] = settings.SUPPORT_EMAIL

        html_message = render_to_string(self.template, context=self.context)
        send_mail_use_broker_task.delay(
            self.email_addresses,
            self.subject,
            html=html_message,
            filename=filename
        )
