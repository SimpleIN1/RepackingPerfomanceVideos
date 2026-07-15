import os
import re
import signal
import logging
import psutil

from django.conf import settings


SAFE_PATH_PATTERN = re.compile(fr'^{settings.DIR_FFMPEG_DATA}/[\d\-T]+$')


def terminate_process(process_name):
    """
    Завершение процесса по имени
    :param process_name:
    :return:
    """

    if not SAFE_PATH_PATTERN.match(process_name):
        logging.error(f"Небезопасное имя процесса: {process_name}")
        return

    try:
        result = os.system(f"pkill -9 -f '{process_name}'")
        logging.info(f"Результат {result}")
    except ProcessLookupError:
        logging.error(f"Процесс с именем {process_name} не найден.")


def terminate_process_psutil(pid) -> None:
    """
    Завершает процесс
    :param pid:
    :return:
    """

    try:
        p = psutil.Process(pid)
        if p.is_running():
            p.terminate()
    except psutil.NoSuchProcess:
        return
