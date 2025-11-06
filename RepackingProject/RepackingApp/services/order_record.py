from typing import List

from django.db.models import Q
from django.db import transaction

from RepackingApp.models import RecordingModel, RecordingTaskIdModel, OrderRecordingModel


def get_recording_orders(filter_query: Q) -> List[OrderRecordingModel]:
    """
    Извлечение заказов
    :param filter_query:
    :return:
    """

    return OrderRecordingModel.objects.filter(filter_query)


def update_recording_orders(filter_query: Q, **data) -> None:
    """
    Обновлeние заказов
    :param filter_query:
    :return:
    """
    with transaction.atomic():
        return OrderRecordingModel.objects.filter(filter_query).update(**data)


def create_recording_order(**data) -> OrderRecordingModel:
    """
    Создает заказ
    :param data:
    :return:
    """

    return OrderRecordingModel.objects.create(**data)


def create_recording_orders(recording_orders: List[OrderRecordingModel]) -> List[OrderRecordingModel]:
    """
    Создает заказы
    :param recording_orders:
    :return:
    """

    return OrderRecordingModel.objects.bulk_create(recording_orders)


def delete_recording_orders(filter_query: Q) -> None:
    """
    Удаление заказов
    :param filter_query:
    :return:
    """

    OrderRecordingModel \
        .objects \
        .filter(filter_query) \
        .delete()
