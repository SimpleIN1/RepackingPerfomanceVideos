import pprint
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


def get_recording_order_tasks_distinct_record(filter_query: Q) -> List[RecordingTaskIdModel]:
    """
    Извлечение recording тасок
    # .select_related("order") на order автоматом подствился inner join блятсво
    :param filter_query:
    :return:
    """

    return RecordingTaskIdModel.objects.filter(filter_query).distinct("recording_id").only("recording_id")


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

    return RecordingTaskIdModel.objects.bulk_create(
        recording_tasks,
        ignore_conflicts=True,
        unique_fields=["task_id"], update_fields=["task_id"]
    )


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
    """
    SELECT
        DISTINCT ON (rt.recording_id)
        rt.recording_id,
        rt.status,
        rt.datetime_created
    FROM "RepackingApp_recordingtaskidmodel" AS rt
    ORDER BY
        rt.recording_id, rt.datetime_created DESC,
        rt.status;

    :param user_id:
    :param type_recording_id:
    :return:
    """
    query_status = (Q(status=4) | Q(status=5) | Q(status=6))

    items = RecordingTaskIdModel \
        .objects \
        .filter(
            Q(order__type_recording_id=type_recording_id)
            & (query_status | (Q(order__user_id=user_id) & ~query_status))
        ) \
        .distinct("recording_id") \
        .order_by("recording_id", "-datetime_created", "status") \
        .values("recording_id", "datetime_created", "status")

    return items
