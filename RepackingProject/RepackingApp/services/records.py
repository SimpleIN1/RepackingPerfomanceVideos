from __future__ import annotations

import datetime
from typing import List, Tuple, Dict

import httplib2
from lxml import etree
from http import HTTPStatus
from urllib.parse import urlsplit, parse_qs, urlencode
from httplib2.error import ServerNotFoundError

from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from common.checksum import calculate_checksum, add_checksum_to_url
from RepackingApp.models import TypeMeetingModel, MeetingModel

URL = "https://vcs-3.ict.sbras.ru/bigbluebutton/api/"
API_CALL = "getRecordings"


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


def parse_xml_type_recording(
    xml_recording: etree._Element
) -> TypeMeetingModel | None:
    """
    Парсинг парсин данных типа конференции
    :param xml_recording:
    :return:
    """

    if not is_xml_element_or_not_none(xml_recording):
        return None

    try:
        name = xml_recording.find("name").text
        return TypeMeetingModel(name=name)
    except AttributeError:
        return None


def parse_xml_recording(
    xml_recording: etree._Element
) -> MeetingModel | None:
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

        return MeetingModel(
            record_id=record_id,
            meeting_id=meeting_id,
            url=url,
            datetime_created=datetime_created,
            datetime_stopped=datetime_stopped,
        )
    except AttributeError:
        return None


def parse_xml_recordings(content: str) -> Dict | None:
    """
    Парсинг списка конференций и типов конференций из xml, формируя словарь с объектами
    MeetingModel, TypeMeetingModel
    :param content:
    :return:
    """

    if is_xml_element_or_none(content):
        return None

    try:
        tree = etree.fromstring(content)
    except etree.XMLSyntaxError:
        return None

    recordings_xml = tree.find("recordings")

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


def upload_recordings_to_db(data: dict) -> Dict | None:
    """
    Загрузка данных в базу данных
    :param data:
    :return:
    """

    if data is None:
        return

    TypeMeetingModel.objects.bulk_create(
        data["type_recordings"], update_conflicts=True,
        unique_fields=["name"], update_fields=["name"]
    )

    for key, recording in data["recordings"]:
        type_meeting = TypeMeetingModel.objects.get(name=key)
        recording.type_meeting = type_meeting

    MeetingModel.objects.bulk_create(
        list(map(lambda x: x[1], data["recordings"])),
        update_conflicts=True,
        unique_fields=["record_id", "meeting_id"],
        update_fields=["record_id", "meeting_id"]
    )

    return data


def get_recordings(**kwargs):
    """
    Извлекает из базы данных конференции
    :param kwargs:
    :return:
    """
    queryset = MeetingModel \
        .objects \
        .select_related("type_meeting") \
        .filter(**kwargs)
    return queryset


def get_recordings_to_dict(fields: list, **filters):
    """
    Извлекает из базы данных конференции, преобразуя в словарь
    :return:
    """

    queryset = MeetingModel \
        .objects \
        .select_related("type_meeting") \
        .filter(**filters) \
        .order_by("datetime_created") \
        .values(*fields)
    return queryset


def get_type_recordings_to_dict():
    """
    Извлекает из базы данных типы конференций, преобразуя в словарь
    :return:
    """
    queryset = TypeMeetingModel \
        .objects \
        .order_by("name") \
        .values("id", "name")
    return queryset


def get_type_recordings(order_by=False):
    """
    Извлекает из базы данных конференции, сортируя по полю "name"
    :param order_by:
    :return:
    """
    return TypeMeetingModel.objects.all().order_by("name")


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


def update_recordings_fields(new_recordings, fields_update: list):
    for recording in new_recordings:
        data = {field: getattr(recording, field) for field in fields_update}
        MeetingModel.objects.filter(record_id=recording.record_id).update(**data)


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

