from typing import List

from django.db.models import Q

from RepackingApp.models import RecodingFileUserModel


def get_recording_files(filter_query: Q) -> List[RecodingFileUserModel]:
    """
    Извлечение записей в соответствии с условием
    :param filter_query:
    :return:
    """

    return RecodingFileUserModel.objects.filter(filter_query)


def get_recording_files_for_upload(filter_query: Q) -> List[RecodingFileUserModel]:
    """
    Извлечение записей в соответствии с условием
    :param filter_query:
    :return:
    """

    return RecodingFileUserModel \
        .objects \
        .select_related("recording_task",
                        "recording_task__recording",
                        "recording_task__recording__type_recording") \
        .filter(filter_query)


def get_download_recording_files(filter_query: Q) -> List[RecodingFileUserModel]:
    """
    Извлечение записей в соответствии с условием
    :param filter_query:
    :return:
    """

    return RecodingFileUserModel \
        .objects \
        .select_related("recording_task",
                        "recording_task__recording",
                        "recording_task__order",
                        "recording_task__recording__type_recording") \
        .filter(filter_query) \
        .only("id",
              "recording_task",
              "recording_task__order__user",
              "recording_task__recording__type_recording__name",
              "recording_task__recording__datetime_created",
              "file_size")


def create_recording_file(**data) -> RecodingFileUserModel:
    """
    Загрука файла конференции
    :param data:
    :return:
    """

    return RecodingFileUserModel.objects.create(**data)


def delete_recording_files(filter_query: Q) -> None:
    """
    Удаление записей в соответствии с условием
    :param filter_query:
    :return:
    """

    RecodingFileUserModel.objects.filter(filter_query).delete()
