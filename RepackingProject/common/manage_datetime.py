from __future__ import annotations

from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone


def from_timestamp(gmp):
    """
    Конвертирование из timrstamp формата в формат даты datetime
    :param gmp:
    :return:
    """
    datetime_tmp = datetime.fromtimestamp(
        float(f"{gmp[:-3]}.{gmp[-3:]}"), tz=timezone.utc
    )
    return datetime_tmp


def current_year():
    """
    Выводит текщий год
    :return:
    """

    return datetime.now(tz=timezone.utc).year


def is_expiration_time(datetime_created: str, minutes: int):
    """
    Проверяет, что не истекло сколько-то минут (e.g. datetime_created = 1763219817)
    :param datetime_created:
    :param minutes:
    :return:
    """

    datetime_created = int(datetime_created)
    return ((datetime.now(timezone.utc) -
             datetime.fromtimestamp(datetime_created, timezone.utc)) <
            timedelta(minutes=minutes))
