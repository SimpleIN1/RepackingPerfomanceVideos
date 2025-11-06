from django.conf import settings
from django.urls import reverse_lazy

from common.code_generator import generate_code
from common.mail.email_user import ConfirmationEmailUser
from AccountApp.services.session_service import ConfirmationCodeSessionService


def send_confirmation_email(cm_user: ConfirmationEmailUser):
    """
    Отправка  и генерация кода по электронной почте
    :param cm_user:
    :return:
    """

    code = generate_code()

    if settings.DEBUG:
        print("CODE:", code)

    ccs = ConfirmationCodeSessionService(cm_user.session, cm_user.user)
    ccs.add(code, cm_user.kind, **cm_user.data)
    ccs.reset_attempt(cm_user.kind)

    session_id = cm_user.session.session_key
    verify_url = f"{settings.SCHEMA}://{settings.DOMAIN}{str(reverse_lazy(cm_user.api_call))}?session_id={session_id}"
    context = {
        "code": code,
        "expiration_minutes": settings.EXPIRATION_MINUTES,
        "verify_url": verify_url
    }
    if settings.EMAIL_SENDER:
        cm_user.callback(cm_user.user.email, context).send()
