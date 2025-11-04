from django.conf import settings
from django.urls import reverse_lazy

from common.mail.email_user import NotifyEmailUser


def send_processed_video_notify_email(nm_user: NotifyEmailUser):
    """
    Отправка уведомления об успешной обработке видеофайлов
    :param nm_user:
    :return:
    """

    session_id = "dfsfsf"
    videos_url = f"{settings.SCHEMA}://{settings.DOMAIN}{str(reverse_lazy(nm_user.api_call))}?session_id={session_id}"
    context = {
        "video_count": nm_user.video_count,
        "videos_url": videos_url
    }
    if settings.EMAIL_SENDER:
        nm_user.callback(nm_user.user.email, context).send()
