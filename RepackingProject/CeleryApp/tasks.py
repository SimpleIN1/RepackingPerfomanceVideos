from __future__ import annotations

import os
import time
import shutil
import logging
import datetime
import subprocess

from django.db.models import Q
from django.conf import settings
from django.db.utils import IntegrityError
from django.core.mail import send_mail, BadHeaderError

from AccountApp.models import UserModel
from AccountApp.services.user import get_user
from CeleryApp.app import app
from RepackingApp.models import RecordingTaskIdModel
from common.archive import Archiving, ArchivingUnpack
from common.nextcloud import upload_to_nextcloud
from common.process_termination import terminate_process
from common.redis_conn import get_redis_connection
from common.mail.email_user import NotifyEmailUser
from RepackingApp.services.record_task import update_recording_tasks, create_recording_task
from RepackingApp.services.order_record import update_recording_orders, get_recording_orders, \
    get_recording_orders_with_type_recording
from RepackingApp.services.notify_email_user import send_processed_video_notify_email
from RepackingApp.services.downloads import create_recording_file, delete_recording_files, get_recording_files
from RepackingApp.services.records import update_recording_by_record_id, \
    upload_recordings_from_source_without_duplicate, get_recordings_foreinkey_type_recording, get_type_recording_by_id


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
def repack_threads_video_task(
    self, resource, user_id, recording_task
):
    """
    Перепакова видео через отложенный вызов
    :param self:
    :param resource:
    :param recording_id:
    :param user_id:
    :return: None
    """

    # Создаем REDIS соединение для ведения подсчета обработанных файлов

    r = get_redis_connection()

    # Извелаем пользователя для проверки возможности загрузки и отправки эп.

    user = get_user(pk=user_id)
    order_id = recording_task["order_id"]
    recording_id = recording_task["recording_id"]

    # Создание задачи
    recording_task["status"] = 3
    recording_task["task_id"] = self.request.id

    try:
        create_recording_task(**recording_task)
        logging.info("Created recording task")
    except IntegrityError:
        logging.info("Update recording task status to 3 value ")
        update_recording_tasks(
            Q(task_id=self.request.id), status=3
        )

    logging.info(f"Start process {resource}, {recording_id}")

    recordings = get_recordings_foreinkey_type_recording(Q(record_id=recording_id))
    first_recording = recordings[0]

    fname_datetime = first_recording.datetime_created.astimezone(settings.TIME_ZONE_PYTZ).strftime('%Y-%m-%dT%H:%M')
    fname = f"{fname_datetime}.mp4"
    unique_fdir = f"{fname_datetime}-{str(time.time()).replace('.', '')}"
    fname_popcorn = f"popcorn.xml"

    local_source_dir = f"files/ffmpeg/{unique_fdir}"
    local_source_file = f"{local_source_dir}/{fname}"
    remote_dir = f"{first_recording.type_recording.name}/{unique_fdir}"

    # Добавляем идентификатор задачи и процессорное имя,
    # чтобы можно было завершить задачу

    r.set(self.request.id, local_source_dir)
    r.save()

    try:
        # Через модуль subprocess запускаем bash script, для обарботки видео потоков
        # через ffmpeg.
        # Файлы сохраняются в директорию files/ffmpeg/

        logging.info("Start process ffmpeg")
        subprocess.run(
            [
                "./scripts/start-repack-ffmpeg.sh",
                "-r", resource,
                "-i", recording_id,
                "-o", local_source_file
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            check=True
        )

        # Обновление статуса задачи на "завершена"

        update_recording_tasks(
            Q(task_id=self.request.id), status=4
        )

        # Загрузка файлов видео конференции и переписки чата в NextCloud хранилище.

        if user.nextcloud_upload:
            logging.info("Start upload to NEXTCLOUD")

            upload_to_nextcloud(
                f"{remote_dir}/{fname}", local_source_file
            )
            upload_to_nextcloud(
                f"{remote_dir}/chat.xml", f"{local_source_dir}/{fname_popcorn}"
            )

            logging.info("Upload successfully")

            # Обновление статуса задачи на "загружена"

            update_recording_tasks(
                Q(task_id=self.request.id), status=5
            )

        # Архивирование. После загрузки файлов в NextCloud хранилище
        # файлы ахрвируются и появляется возможность скачать по ссылке.

        a = Archiving(path=local_source_dir, expansion="zip")
        filename = a.make_archive()
        logging.info(f"Create archive {filename}")

        # Добавление информации в базу данных о созданном архиве,
        # чтобы иметь возможность скачать.

        create_recording_file(recording_task_id=self.request.id,
                              file=filename,
                              file_size=os.path.getsize(filename))

        logging.info("Upload to db recording file")

        # Рекурсивная очистка директорий (с видео и перепиской)

        shutil.rmtree(local_source_dir)

        logging.info(f"Stop process {resource}, {recording_id}")

        r.incr(settings.REDIS_KEY_ORDER_PROCESSED.format(order_id))

    except (FileNotFoundError, subprocess.CalledProcessError) as f:
        logging.error(f)

        # Обновление статусов, очистка директорий из-за ошибки

        r.incr(settings.REDIS_KEY_ORDER_FAILED.format(order_id))

        update_recording_tasks(
            Q(task_id=self.request.id), status=6
        )

        r.delete(self.request.id)
        r.save()

        shutil.rmtree(local_source_dir)


@app.task
def upload_processed_records(task_id, user_id, type_recording_name, local_source_file):
    """
    Загрузка обработных записей
    :param task_id:
    :param user_id:
    :param type_recording_name:
    :param local_source_file:
    :return:
    """
    user = get_user(pk=user_id)

    if user.nextcloud_upload:
        try:
            logging.info("Start upload to NEXTCLOUD")

            extract_dir = os.path.basename(local_source_file).split('.')[0]
            fname = f"{'-'.join(extract_dir.split('-')[0:3])}.mp4"
            local_source_dir = os.path.join(os.path.dirname(local_source_file), extract_dir)
            remote_file = f"{type_recording_name}/{extract_dir}/{fname}"

            a = ArchivingUnpack(local_source_file)
            a.unpack_archive()

            upload_to_nextcloud(
                remote_file, f"{local_source_dir}/{fname}"
            )
            upload_to_nextcloud(
                f"{type_recording_name}/{extract_dir}/chat.xml", f"{local_source_dir}/popcorn.xml"
            )

            shutil.rmtree(local_source_dir)

            logging.info("Upload successfully")

            update_recording_tasks(
                Q(task_id=task_id), status=5
            )
        except FileNotFoundError as f:
            logging.error(f)
            logging.warning("PASS PASS PASS")

            if os.path.exists(local_source_dir):
                shutil.rmtree(local_source_dir)

            update_recording_tasks(
                Q(task_id=task_id), status=6
            )


@app.task
def upload_recordings_periodic_task():
    """
    Переодическа задача загрузки данных о новых конференциях
    :return:
    """

    logging.info("Start uploading recordings periodic task")
    upload_recordings_from_source_without_duplicate(settings.BBB_RESOURCE)
    logging.info("Stop uploading recordings periodic task")


@app.task
def remove_expired_files_periodic_task():
    """
    Переодическая задача удаления архивов, у которых истек срок жизни
    :return:
    """

    logging.info("Start remove recordings files periodic task")
    query_filter = Q(
        datetime_created__lte=
        datetime.datetime.now(datetime.timezone.utc)
        -
        datetime.timedelta(days=7)
    )
    logging.info("Get recordings files")
    recording_files = get_recording_files(query_filter)
    tasks = [item.recording_task_id for item in recording_files]
    update_recording_tasks(Q(task_id__in=tasks) & ~Q(status=5), status=1)

    try:
        logging.info("Start remove files from storage")
        for item in recording_files:
            logging.info(f"Remove {item.file}")
            if os.path.exists(item.file):
                os.remove(item.file)

        logging.info("Start remove files from db")
        delete_recording_files(query_filter)
    except FileNotFoundError as e:
        logging.error(e)

    logging.info("Stop remove recordings files periodic task")


@app.task
def remove_dirs_task(dirnames):
    """
    Удаление директорий
    :param dirnames:
    :return:
    """
    logging.info("Start remove dir task")

    try:
        for dirname in dirnames:
            logging.info(f"Remove {dirname}")
            if os.path.exists(dirname):
                shutil.rmtree(dirname)
    except FileNotFoundError as e:
        logging.error(e)

    logging.info("Stop remove dir task")


@app.task
def terminate_process_task(tasks):
    """
    Завершение celery процессов.
    :param tasks:
    :return:
    """

    logging.info("Start terminate_process_task")

    dirnames = []
    with get_redis_connection() as r:
        for task_id in tasks:
            process_name = r.get(task_id)
            logging.info(f"Stop PROCESS {process_name}")
            r.delete(task_id)
            if process_name:
                process_name = process_name.decode('utf-8')
                terminate_process(process_name)
                dirnames.append(process_name)

    if dirnames:
        remove_dirs_task.delay(dirnames)

    logging.info("Stop terminate_process_task")


@app.task
def check_count_processed_videos_periodic_task():
    """
    Отправка уведомления об обработанных файлах.
    Извлекаются количественные параметры обработки: сколько обработано,
    сколько неудачно обработанных файлов.
    Делается запрос в базу данных, чтобы получить тип конференции.
    Формируется объект с параметрами для отправки по эп.
    :return:
    """

    logging.info("Start check_count_processed_videos_periodic_task")
    orders = get_recording_orders_with_type_recording(Q(processed=False), fields=["type_recording__name"])

    if not orders:
        return

    r = get_redis_connection()

    for order in orders:

        count_encode = r.get(settings.REDIS_KEY_ORDER_PROCESSED.format(order.id))
        count = int(count_encode.decode("utf-8")) if count_encode else 0

        count_cancelled_encode = r.get(settings.REDIS_KEY_ORDER_CANCELLED.format(order.id))
        count_cancelled = int(count_cancelled_encode.decode("utf-8")) if count_cancelled_encode else 0

        count_failed_encode = r.get(settings.REDIS_KEY_ORDER_FAILED.format(order.id))
        count_failed = int(count_failed_encode.decode("utf-8")) if count_failed_encode else 0

        logging.warning(f"order_id {order.id}, {order.count}, count_cancelled {count_cancelled}, count proc {count}, count_failed {count_failed}")

        if order.count == count + count_cancelled + count_failed:
            logging.info(f"Count {count} PROCESSED order {order.id}")

            r.delete(settings.REDIS_KEY_ORDER_FAILED.format(order.id))
            r.delete(settings.REDIS_KEY_ORDER_CANCELLED.format(order.id))
            r.delete(settings.REDIS_KEY_ORDER_PROCESSED.format(order.id))
            r.save()

            update_recording_orders(Q(pk=order.id), count_failed=count_failed,
                                    count_canceled=count_cancelled, processed=True)

            if count > 0:
                from common.mail.mail import NotifyProcessedRecordsEmail
                nm = NotifyEmailUser(video_count=order.count,
                                     video_count_failed=count_failed,
                                     video_count_cancelled=count_cancelled,
                                     type_name=order.type_recording.name,
                                     user=order.user,
                                     session=None,
                                     kind=None,
                                     api_call="repacking-downloads",
                                     callback=NotifyProcessedRecordsEmail)
                send_processed_video_notify_email(nm)

    logging.info(f"Stop {order.id} check_count_processed_videos_periodic_task")

###  Session storage