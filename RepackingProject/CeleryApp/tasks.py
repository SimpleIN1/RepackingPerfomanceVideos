from __future__ import annotations

import datetime
import logging
import subprocess

from django.conf import settings
from django.db.models import Q
from django.core.mail import send_mail, BadHeaderError

from CeleryApp.app import app
from common.nextcloud import upload_to_nextcloud
from common.redis_conn import get_redis_connection
from RepackingApp.services.records import update_recording_by_record_id, \
    upload_recordings_from_source_without_duplicate, get_recordings_foreinkey_type_recording


@app.task
def send_mail_use_broker_task(
        email_addresses: str | list,
        subject: str,
        message: str = None,
        html: str = None,
        filename: str = None
) -> None:
    """
    Отправка электронного письма
    :param email_addresses:
    :param subject:
    :param message:
    :param html:
    :param filename:
    :return:
    """
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


@app.task(bind=True)
def repack_threads_video_task(self, resource, recording_id):
    """
    Перепакова видео через отложенный вызов
    :param self:
    :param resource:
    :param recording_id:
    :return:
    """

    logging.info(f"Start process {resource}, {recording_id}")
    update_recording_by_record_id(recording_id, status=3)
    recordings = get_recordings_foreinkey_type_recording(Q(record_id=recording_id))
    fname = f"{recordings[0].datetime_created.strftime('%Y-%m-%dT%H:%M')}.mp4"
    local_source_file = f"files/ffmpeg/{fname}"

    p = subprocess.Popen(
        [
            "./scripts/start-repack-ffmpeg.sh",
            "-r", resource,
            "-i", recording_id,
            "-o", local_source_file
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT
    )
    logging.info(f"pid: {p.pid}")
    with get_redis_connection() as r:
        r.set(self.request.id, p.pid)
        r.save()

    while True:
        try:
            p.wait(1)
        except subprocess.TimeoutExpired:
            pass
        else:
            break

    update_recording_by_record_id(recording_id, status=4)

    logging.info("Start upload to NEXTCLOUD")

    remote_file = f"{recordings[0].type_recording.name}/{fname}"
    upload_to_nextcloud(remote_file, local_source_file)

    logging.info("Upload successfully")

    update_recording_by_record_id(recording_id, status=5)

    logging.info(f"Stop process {resource}, {recording_id}")


@app.task
def upload_recordings_periodic_task():
    logging.info("Start uploading recordings periodic task")
    upload_recordings_from_source_without_duplicate(settings.BBB_RESOURCE)
    logging.info("Stop uploading recordings periodic task")


###   возможость скачивания с сервера!?
###   Загрузка на mydisk.
###   подгрузка текстовых сообщений (формирование архива с текстовыми сообщениями и видео)