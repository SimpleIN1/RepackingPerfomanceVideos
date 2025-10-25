
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

app.conf.beat_schedule = {
    # 'Parse crypto currencies every 10 minutes': {
    #     'task': 'CeleryApp.tasks.parse_crypto_currencies',
    #     'schedule': crontab(minute='20', )
    # },

    # 'Delete users are not verify every 2 hours': {
    #     'task': 'AccountApp.tasks.clear_not_verify_user',
    #     'schedule': crontab(hour='2')
    # },

    # 'Delete codes are not verify every 2 hours': {
    #     'task': 'AccountApp.tasks.clear_reset_code_not_verify',
    #     'schedule': crontab(hour='2')
    # },
}


# @worker_ready.connect
# def at_start(sender, **kwargs):
#     logging.info('Start worker_ready At_start')
#     with sender.app.connection() as conn:
#         sender.app.send_task('CeleryApp.tasks.parse_crypto_currencies', connection=conn)
#         sender.app.send_task('AccountApp.tasks.clear_not_verify_user', connection=conn)
#         sender.app.send_task('AccountApp.tasks.clear_reset_code_not_verify', connection=conn)
