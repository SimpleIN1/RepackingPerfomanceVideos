from __future__ import annotations

import os
import time
import redis
import random
import signal
import logging
import subprocess

from django.conf import settings
from django.core.cache import cache
from celery.contrib import abortable
from django.core.mail import send_mail, BadHeaderError
from django.contrib.sessions.backends.db import SessionStore

from CeleryApp.app import app
from RepackingApp.models import RecordingModel
from common.redis_conn import get_redis_connection
from RepackingApp.services.records import update_recording_by_record_id, upload_recordings_from_source_without_duplicate


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

    p = subprocess.Popen(
        [
            "./scripts/start-repack-ffmpeg.sh",
            "-r", resource,
            "-i", recording_id,
            "-o", "files/ffmpeg"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT
    )
    logging.info(f"pid: {p.pid}")
    with get_redis_connection() as r:
        r.set(self.request.id, p.pid)
        logging.info(r.get(self.request.id))
        r.save()

    while True:
        try:
            p.wait(1)
        except subprocess.TimeoutExpired:
            pass
        else:
            break

    logging.info("CONTINUE")
    update_recording_by_record_id(recording_id, status=4)
    logging.info(f"Stop process {resource}, {recording_id}")


@app.task
def upload_recordings_periodic_task():
    logging.info("Start uploading recordings periodic task")
    upload_recordings_from_source_without_duplicate(settings.BBB_RESOURCE)
    logging.info("Stop uploading recordings periodic task")


### Загрузка на mydisk.
### подгрузка текстовых сообщений