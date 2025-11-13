
import os
import logging

from celery import Celery
from celery.signals import worker_ready
from celery.schedules import crontab
from django.apps import apps
from django.conf import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RepackingProject.settings')
app = Celery('CeleryApp', broker=settings.BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])
app.conf.broker_connection_retry_on_startup = True


# Распеределение задач по очередям
app.conf.task_routes = {
    'CeleryApp.tasks.upload_recordings_periodic_task': {
        'queue': 'common_worker_queue'
    },
    'CeleryApp.tasks.send_mail_use_broker_task': {
        'queue': 'common_worker_queue'
    },
    'CeleryApp.tasks.remove_expired_files_periodic_task': {
        'queue': 'common_worker_queue'
    },
    'CeleryApp.tasks.remove_dirs_task': {
        'queue': 'common_worker_queue'
    },
    'CeleryApp.tasks.check_count_processed_videos_periodic_task': {
        'queue': 'common_worker_queue'
    },
    'CeleryApp.tasks.repack_threads_video_task': {
        'queue': 'ffmpeg_worker_queue'
    },
    'CeleryApp.tasks.terminate_process_task': {
        'queue': 'ffmpeg_worker_queue'
    },
    'CeleryApp.tasks.upload_processed_records': {
        'queue': 'upload_worker_queue'
    }
}

app.conf.beat_schedule = {
    'Upload recordings every hour': {
        'task': 'CeleryApp.tasks.upload_recordings_periodic_task',
        'schedule': 60*60,
    },
    'Check files and remove every 1.5 hour': {
        'task': 'CeleryApp.tasks.remove_expired_files_periodic_task',
        'schedule': 60*90,
    },
    'Check orders every 10 minutes': {
        'task': 'CeleryApp.tasks.check_count_processed_videos_periodic_task',
        'schedule': 60*10,
    },
}
