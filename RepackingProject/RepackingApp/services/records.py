from __future__ import annotations

import pprint
from typing import List, Tuple, Dict

import httplib2
from lxml import etree
from http import HTTPStatus
from urllib.parse import urlsplit, parse_qs, urlencode
from httplib2.error import ServerNotFoundError

from django.conf import settings
from django.db.models import Q
from django.db import transaction
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from common.manage_datetime import from_timestamp
from common.checksum import calculate_checksum, add_checksum_to_url
from RepackingApp.models import TypeRecordingModel, RecordingModel, RecordingTaskIdModel


def is_xml_element_or_not_none(value) -> bool:
    """
    Проверка на неопределенное значние и объекта элемента lxml
    :param value:
    :return:
    """

    return value is not None or isinstance(value, etree._Element)


def is_xml_element_or_none(value) -> bool:
    """
    Проверка на неопределенное значние и объекта элемента lxml
    :param value:
    :return:
    """

    return value is None or isinstance(value, etree._Element)


def parse_xml_type_recording(xml_recording: etree._Element) -> TypeRecordingModel | None:
    """
    Парсинг парсин данных типа конференции
    :param xml_recording:
    :return:
    """

    if not is_xml_element_or_not_none(xml_recording):
        return None

    try:
        name = xml_recording.find("name").text
        return TypeRecordingModel(name=name)
    except AttributeError:
        return None


def parse_xml_recording(xml_recording: etree._Element) -> RecordingModel | None:
    """
    Парсинг парсин данных конференции
    :param xml_recording:
    :return:
    """

    if not is_xml_element_or_not_none(xml_recording):
        return None

    try:
        record_id = xml_recording.find("recordID").text
        meeting_id = xml_recording.find("meetingID").text
        url = xml_recording.find("playback").find("format").find("url").text.strip(' \n')
        datetime_created = from_timestamp(xml_recording.find("startTime").text)
        datetime_stopped = from_timestamp(xml_recording.find("endTime").text)

        return RecordingModel(
            record_id=record_id,
            meeting_id=meeting_id,
            url=url,
            datetime_created=datetime_created,
            datetime_stopped=datetime_stopped,
        )
    except AttributeError:
        return None


def to_xml_recording(content: str) -> etree._Element | None:
    if is_xml_element_or_none(content):
        return None

    try:
        tree = etree.fromstring(content)
    except etree.XMLSyntaxError:
        return None

    recordings_xml = tree.find("recordings")

    if recordings_xml is None:
        return None

    return recordings_xml


def parse_xml_recordings(content: str) -> Dict | None:
    """
    Парсинг списка конференций и типов конференций из xml, формируя словарь с объектами
    RecordingModel, TypeRecordingModel
    :param content:
    :return:
    """

    recordings_xml = to_xml_recording(content)
    if recordings_xml is None:
        return None

    recordings = []
    type_recordings = []
    for index, xml_recording in enumerate(recordings_xml):
        type_recording = parse_xml_type_recording(xml_recording)
        type_recordings.append(type_recording)

        recording = parse_xml_recording(xml_recording)

        if not recording:
            continue

        recordings.append((type_recording.name, recording))

    return {
        "recordings": recordings,
        "type_recordings": type_recordings
    }


def parse_xml_only_recordings_dict(content: str) -> Dict | None:
    """
    Парсинг списка конференций и типов конференций из xml, формируя словарь с объектами
    RecordingModel, TypeRecordingModel
    :param content:
    :return:
    """

    recordings_xml = to_xml_recording(content)
    if recordings_xml is None:
        return None

    recordings = {}
    for index, xml_recording in enumerate(recordings_xml):
        type_recording = parse_xml_type_recording(xml_recording)
        recording = parse_xml_recording(xml_recording)

        if not recording:
            continue

        recordings[recording.record_id] = {
            "recording": recording,
            "type_recording": type_recording
        }

    return {
        "recordings": recordings
    }


def request_recordings(url: str) -> str | None:
    """
    Выполняется запрос на сервер с записями о конференциях
    :param url:
    :return:
    """

    url_validator = URLValidator()

    try:
        url_validator(url)
    except ValidationError:
        return None

    http = httplib2.Http()
    headers = {'content-type': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

    try:
        resp, content = http.request(url, "GET", headers=headers)
    except ServerNotFoundError:
        return None

    expected_content_type = "text/xml"
    if expected_content_type not in resp["content-type"]:
        return None

    if resp.status != HTTPStatus.OK:
        return None

    return content


def get_recording(recording_id: str) -> RecordingModel | None:
    """
    Извлечение записи из базы данных по recording_id
    :param recording_id:
    :return:
    """

    try:
        recording = RecordingModel.objects.get(record_id=recording_id)
        return recording
    except RecordingModel.DoesNotExist:
        return None


def get_recordings_foreinkey_type_recording(filter_query: Q) -> List[RecordingModel]:
    """
    Извлекает из базы данных конференции с использованием соедения с таблицей type_recording
    :param kwargs:
    :return:
    """
    queryset = RecordingModel \
        .objects \
        .select_related("type_recording") \
        .filter(filter_query)
    return queryset


def get_recordings(filter_query: Q) -> List[RecordingModel]:
    """
    Извлекает из базы данных конференции
    :param filter_query:
    :return:
    """
    queryset = RecordingModel \
        .objects \
        .filter(filter_query)
    return queryset


def get_recordings_to_dict(fields: List[str], filter_query: Q):
    """
    Извлекает из базы данных конференции, преобразуя в словарь
    :return:
    """

    queryset = RecordingModel \
        .objects \
        .select_related("type_recording") \
        .filter(filter_query) \
        .order_by("datetime_created") \
        .values(*fields)
    return queryset


def get_recordings_to_dict_with_status(fields: List[str], filter_query: Q):
    """
    Извлекает из базы данных конференции, преобразуя в словарь
    :return:
    """

    queryset = RecordingTaskIdModel \
        .objects \
        .select_related("recording", "order") \
        .filter(filter_query)

    # print(RecordingModel.objects.all().filter(recordingtaskidmodel__order__user_id=1).query)

    return queryset


def get_type_recordings_to_dict(fields: list) -> List[TypeRecordingModel]:
    """
    Извлекает из базы данных типы конференций, преобразуя в словарь
    :return:
    """
    queryset = TypeRecordingModel \
        .objects \
        .order_by("name") \
        .values(*fields)
    return queryset


def get_type_recordings(order_by=False):
    """
    Извлекает из базы данных конференции, сортируя по полю "name"
    :param order_by:
    :return:
    """
    return TypeRecordingModel.objects.all().order_by("name")


def get_type_recording_by_id(id) -> TypeRecordingModel | None:
    """
    Извлекает из базы данных тип конференции
    :param id:
    :return:
    """
    try:
        return TypeRecordingModel.objects.get(pk=id)
    except TypeRecordingModel.DoesNotExist:
        return None


def update_recording_by_record_id(recording_id: str, **data) -> None:
    """
    Обновление записи по его recording_id
    :param recording_id:
    :param data:
    :return:
    """
    with transaction.atomic():
        RecordingModel.objects.filter(record_id=recording_id).update(**data)


def update_recordings(filter_query: Q, **data) -> None:
    """
    Обновление записей
    :param filter_query:
    :param data:
    :return:
    """

    with transaction.atomic():
        RecordingModel.objects.filter(filter_query).update(**data)


def update_recordings_fields(new_recordings, fields_update: list):
    """

    :param new_recordings:
    :param fields_update:
    :return:
    """
    for recording in new_recordings:
        data = {field: getattr(recording, field) for field in fields_update}
        RecordingModel.objects.filter(record_id=recording.record_id).update(**data)


def upload_recordings_to_db(data: dict) -> Dict | None:
    """
    Загрузка данных в базу данных
    :param data: {
        "recordings": (tuple(str, RecordingModel)),
        "type_recordings": [TypeRecordingModel]
    }
    :return:
    """

    if data is None:
        return

    TypeRecordingModel.objects.bulk_create(
        data["type_recordings"],
        # update_conflicts=True,
        ignore_conflicts=True,
        unique_fields=["name"], update_fields=["name"]
    )

    type_recording_ids = []
    for key, recording in data["recordings"]:
        type_recording = TypeRecordingModel.objects.get(name=key)
        type_recording_ids.append(type_recording.id)
        recording.type_recording = type_recording

    for i in type_recording_ids:
        cache.delete(settings.CACHE_PK_RECORDINGS.format(i))

    RecordingModel.objects.bulk_create(
        list(map(lambda x: x[1], data["recordings"])),
        # update_conflicts=True,
        ignore_conflicts=True,
        unique_fields=["record_id"], update_fields=["record_id"]
    )

    return data


def upload_from_source(resource):
    url = f"https://{resource}/bigbluebutton/api/getRecordings"
    url = add_checksum_to_url(url)

    response = request_recordings(url)
    if not response:
        return None

    data = parse_xml_recordings(response)

    if not data:
        return None

    return upload_recordings_to_db(data)


def upload_recordings_and_update_fields() -> None:
    url = "https://vcs-3.ict.sbras.ru/bigbluebutton/api/getRecordings"
    url = add_checksum_to_url(url)

    response = request_recordings(url)

    if not response:
        return None

    data = parse_xml_recordings(response)

    if not data:
        return None

    recordings = [item[1] for item in data["recordings"]]
    update_recordings_fields(recordings, ["url"])


def upload_recordings_from_source_without_duplicate(resource):
    url = settings.BBB_URL.format(resource)
    url = add_checksum_to_url(url)

    response = request_recordings(url)
    if not response:
        return None

    data = parse_xml_only_recordings_dict(response)
    if not data:
        return None

    recordings = data.get("recordings")
    if not recordings:
        return None

    recordings_db = RecordingModel.objects.all().values("record_id")
    recordings_ids_db = set(map(lambda x: x["record_id"], recordings_db))
    recordings_ids = set(recordings.keys())
    empty_recordings = recordings_ids.difference(recordings_ids_db)

    if not empty_recordings:
        return None

    type_recordings_db = set(map(lambda x: x.name, TypeRecordingModel.objects.all()))
    type_recordings_names = set(map(lambda x: x.name, parse_xml_recordings(response)["type_recordings"]))
    empty_type_recordings = type_recordings_names.difference(type_recordings_db)

    if empty_type_recordings:
        cache.delete(settings.CACHE_TYPE_RECORDINGS)

    creating_data = {
        "recordings": [],
        "type_recordings": []
    }

    for recording_id in empty_recordings:
        type_recording = recordings[recording_id]["type_recording"]
        creating_data["recordings"].append((type_recording.name, recordings[recording_id]["recording"]))

    creating_data["type_recordings"] = [TypeRecordingModel(name=name) for name in empty_type_recordings]

    return upload_recordings_to_db(creating_data)
