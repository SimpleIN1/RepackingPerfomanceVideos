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
