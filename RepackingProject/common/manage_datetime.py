import datetime

from django.utils import timezone


def from_timestamp(gmp):
    """
    Конвертирование из timrstamp формата в формат даты datetime
    :param gmp:
    :return:
    """
    datetime_tmp = datetime.datetime.fromtimestamp(
        float(f"{gmp[:-3]}.{gmp[-3:]}"), tz=timezone.utc
    )
    return datetime_tmp


def current_year():
    return datetime.datetime.now(tz=timezone.utc).year
