
from django.conf import settings

from common.mail.mail_sender import SenderEmail


class Confirmation2FAEmail(SenderEmail):
    template = "mail/confirmation-code.html"
    subject = f"Подтверждение входа 2FA — {settings.WEBSITE_NAME}"


class ConfirmationEmail(SenderEmail):
    template = "mail/confirmation-code.html"
    subject = f"Подтверждение email адреса — {settings.WEBSITE_NAME}"


class ConfirmationForgotPasswordEmail(SenderEmail):
    template = "mail/confirmation-code.html"
    subject = f"Восстановление пароля — {settings.WEBSITE_NAME}"
