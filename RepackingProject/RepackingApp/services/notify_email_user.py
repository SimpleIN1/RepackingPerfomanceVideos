from datetime import datetime

from django.conf import settings
from django.urls import reverse_lazy
from django.contrib.sessions.backends.cache import SessionStore # cache

from common.mail.email_user import NotifyEmailUser


def send_processed_video_notify_email(nm_user: NotifyEmailUser):
    """
    Отправка уведомления об успешной обработке видеофайлов
    :param nm_user:
    :return:
    """

    s = SessionStore()
    s.update({
        settings.NOTIFY_CODE_SESSION: {
            "datetime_created": str(datetime.now().timestamp()).split('.')[0],
            "user_id": nm_user.user.id
        }
    })
    s.save()

    # s = SessionStore()
    # s.update({"session_id": session_id, "datetime_created": str(datetime.now().timestamp()).split('.')[0]})
    # s.save()

    videos_url = f"{settings.SCHEMA}://{settings.DOMAIN}:{settings.PORT}{str(reverse_lazy(nm_user.api_call))}?session_id={s.session_key}"
    context = {
        "video_count": nm_user.video_count,
        "video_count_success": nm_user.video_count-nm_user.video_count_failed-nm_user.video_count_cancelled,
        "video_count_cancelled": nm_user.video_count_cancelled,
        "video_count_failed": nm_user.video_count_failed,
        "type_name": nm_user.type_name,
        "videos_url": videos_url,
        "share_link": settings.NEXTCLOUD_SHARE_LINK,
        "share_link_password": settings.NEXTCLOUD_SHARE_LINK_PASSWORD
    }
    if settings.EMAIL_SENDER:
        nm_user.callback(nm_user.user.email, context).send()
