from __future__ import annotations

import logging
import random
import time

from django.conf import settings
from django.core.mail import send_mail, BadHeaderError

from CeleryApp.app import app


@app.task
def send_mail_use_broker(
    email_addresses: str | list,
    subject: str,
    message: str =None,
    html: str =None,
    filename: str =None
) -> None:
    logging.info(f"EMAIL {email_addresses}, {subject}")
    if not isinstance(email_addresses, list):
        email_addresses = [email_addresses]

    try:
        logging.info(f"EMAIL {email_addresses}, {subject}")
        send_mail(
            subject=subject,
            message=message,
            html_message=html,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=email_addresses,
            fail_silently=False,
        )
        logging.info('|||->sending mail is success<-|||')
    except BadHeaderError:
        logging.warning('|||->The your mail is sent with failed.<-|||')


@app.task
def common_task_use_broker(*args):
    time.sleep(random.randint(6, 9))


# периодичная таска
# таска постановки в очередь обаботки видео потока
# ...
# ...

