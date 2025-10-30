from typing import List

from django.db.models import Q

from RepackingApp.models import RecordingModel, RecordingTaskIdModel


def get_recording_tasks(filter_query: Q) -> List[RecordingTaskIdModel]:
    """
    Извлечение recording тасок
    :param filter_query:
    :return:
    """

    return RecordingTaskIdModel.objects.filter(filter_query)


def update_recording_tasks(filter_query: Q, **data) -> None:
    """
    Обновлeние recording тасок
    :param filter_query:
    :return:
    """

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
