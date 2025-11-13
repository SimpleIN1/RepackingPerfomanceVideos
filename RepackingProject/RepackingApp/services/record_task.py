from typing import List

from django.db.models import Q
from django.db import transaction

from RepackingApp.models import RecordingModel, RecordingTaskIdModel


def get_recording_tasks(filter_query: Q) -> List[RecordingTaskIdModel]:
    """
    Извлечение recording тасок
    :param filter_query:
    :return:
    """

    return RecordingTaskIdModel.objects.filter(filter_query)


def get_recording_tasks_left_outer_recording(filter_query: Q) -> List[RecordingTaskIdModel]:
    """
    Извлечение recording тасок левое внешенее ограничение
    :param filter_query:
    :return:
    """

    return RecordingModel \
        .objects \
        .filter(filter_query) \
        .values("type_recording", "record_id", "recordingtaskidmodel__status", "url")


def get_recording_order_tasks(filter_query: Q) -> List[RecordingTaskIdModel]:
    """
    Извлечение recording тасок
    :param filter_query:
    :return:
    """

    return RecordingTaskIdModel.objects.select_related("order").filter(filter_query)


def update_recording_tasks(filter_query: Q, **data) -> None:
    """
    Обновлeние recording тасок
    :param filter_query:
    :return:
    """

    with transaction.atomic():
        return RecordingTaskIdModel.objects.filter(filter_query).update(**data)


def create_recording_task(**data) -> RecordingTaskIdModel:
    """
    Создает таску конференции
    :param data:
    :return:
    """

    return RecordingTaskIdModel.objects.create(**data)


def create_recording_tasks(recording_tasks: List[RecordingTaskIdModel]) -> List[RecordingTaskIdModel]:
    """
    Создает таски конференции
    :param recording_tasks:
    :return:
    """

    return RecordingTaskIdModel.objects.bulk_create(recording_tasks)


def delete_recordings_tasks(filter_query: Q) -> None:
    """
    Удаление recording таски
    :param filter_query:
    :return:
    """

    RecordingTaskIdModel \
        .objects \
        .filter(filter_query) \
        .delete()


def get_recording_tasks_status(user_id, type_recording_id):
    query_status = (Q(status=4) | Q(status=5) | Q(status=6))

    items = RecordingTaskIdModel \
        .objects \
        .select_related("order", "recording") \
        .filter(
        Q(recording__type_recording_id=type_recording_id) &
        (query_status | (Q(order__user_id=user_id) & ~query_status))
    ) \
        .values("recording_id", "status", "datetime_created")

    if not items:
        return []

    recording_task_d = {}
    for item in items:
        rid = item["recording_id"]
        checker = False
        if recording_task_d.get(rid):
            if recording_task_d[rid]["datetime_created"] < item["datetime_created"]:
                checker = True
        else:
            checker = True

        if checker:
            recording_task_d[rid] = item

    return recording_task_d
