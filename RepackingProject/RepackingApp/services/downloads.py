from typing import List, Dict

from django.db.models import Q

from RepackingApp.models import RecodingFileUserModel


def get_recording_files(filter_query: Q) -> List[RecodingFileUserModel]:
    """
    Извлечение записей в соответствии с условием
    :param filter_query:
    :return:
    """

    return RecodingFileUserModel.objects.filter(filter_query)


def get_recording_files_for_upload(filter_query: Q) -> Dict[str, RecodingFileUserModel]:
    """
    Извлечение записей в соответствии с условием
    :param filter_query:
    :return: dict {
        "recording_id": RecodingFileUserModel,
    }
    """

    recording_files = RecodingFileUserModel \
        .objects \
        .select_related("recording_task",
                        "recording_task__recording",
                        "recording_task__recording__type_recording") \
        .filter(filter_query)

    recording_files_d = {}
    for item in recording_files:
        rid = item.recording_task.recording_id
        checker = False
        if recording_files_d.get(rid):
            if recording_files_d[rid].datetime_created < item.datetime_created:
                checker = True
        else:
            checker = True

        if checker:
            recording_files_d[rid] = item

    return recording_files_d


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
              "file_size") \
        .order_by("recording_task__recording__type_recording__name")


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
