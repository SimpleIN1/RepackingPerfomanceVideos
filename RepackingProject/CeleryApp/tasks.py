from __future__ import annotations

import os
import time
import shutil
import logging
import datetime
import subprocess

from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail, BadHeaderError

from CeleryApp.app import app
from common.archive import Archiving
from common.nextcloud import upload_to_nextcloud
from common.redis_conn import get_redis_connection
from RepackingApp.services.downloads import create_recording_file, delete_recording_files, get_recording_files
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
def repack_threads_video_task(self, resource, recording_id, user_id):
    """
    Перепакова видео через отложенный вызов
    :param self:
    :param resource:
    :param recording_id:
    :return: None
    """

    logging.info(f"Start process {resource}, {recording_id}")

    update_recording_by_record_id(recording_id, status=3)

    recordings = get_recordings_foreinkey_type_recording(Q(record_id=recording_id))

    fname_datetime = recordings[0].datetime_created.astimezone(settings.TIME_ZONE_PYTZ).strftime('%Y-%m-%dT%H:%M')
    fname = f"{fname_datetime}.mp4"
    unique_fdir = f"{fname_datetime}-{str(time.time()).replace('.', '')}"
    fname_popcorn = f"popcorn.xml"

    local_source_dir = f"files/ffmpeg/{unique_fdir}"
    remote_dir = f"{recordings[0].type_recording.name}/{unique_fdir}"

    p = subprocess.Popen(
        [
            "./scripts/start-repack-ffmpeg.sh",
            "-r", resource,
            "-i", recording_id,
            "-o", f"{local_source_dir}/{fname}"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT
    )

    logging.info(f"pid: {p.pid}")
    with get_redis_connection() as r:
        r.set(self.request.id, p.pid)  # Идентификатор задачи и pid процесса для завершения
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

    upload_to_nextcloud(
        f"{remote_dir}/{fname}", f"{local_source_dir}/{fname}"
    )
    upload_to_nextcloud(
        f"{remote_dir}/chat.xml", f"{local_source_dir}/{fname_popcorn}"
    )

    logging.info("Upload successfully")

    a = Archiving(path=local_source_dir, expansion="zip")
    filename = a.make_archive()
    logging.info(f"Create archive {filename}")

    create_recording_file(user_id=user_id,
                          recording_id=recording_id,
                          file=filename)

    logging.info("upload to db recording file")

    shutil.rmtree(local_source_dir)

    update_recording_by_record_id(recording_id, status=5)

    logging.info(f"Stop process {resource}, {recording_id}")


@app.task
def upload_recordings_periodic_task():
    logging.info("Start uploading recordings periodic task")
    upload_recordings_from_source_without_duplicate(settings.BBB_RESOURCE)
    logging.info("Stop uploading recordings periodic task")


@app.task
def remove_expired_one_day_files_periodic_task():
    logging.info("Start remove recordings files periodic task")
    query_filter = Q(
        datetime_created__lte=
            datetime.datetime.now(datetime.timezone.utc)
            -
            datetime.timedelta(days=1)
    )
    logging.info("Get recordings files")
    recording_files = get_recording_files(query_filter)

    try:
        logging.info("Start remove files from storage")
        for item in recording_files:
            os.remove(item.file)

        logging.info("Start remove files from db")
        delete_recording_files(query_filter)
    except FileNotFoundError as e:
        logging.error(e)

    logging.info("Stop remove recordings files periodic task")

###   возможость скачивания с сервера!?
###   кэширование
###   удаление ненужых файлов
