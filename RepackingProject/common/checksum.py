from __future__ import annotations

import hashlib
from urllib.parse import urlsplit, parse_qs, urlencode

try:
    from django.conf import settings as conf, settings
    from core import dynamic_settings
except ModuleNotFoundError:
    pass


def calculate_checksum(string: str, shared_secret: str = None) -> str:
    """
    Вычисляет checksum по string (строка с параметрами) и shared_secret
    :param string: str
    :param shared_secret: str
    :return: str
    """

    string_b = string.encode("utf-8")

    if not shared_secret:
        shared_secret = dynamic_settings.BBB_SHARED_SECRET
    shared_secret_b = shared_secret.encode("utf-8")

    hb = hashlib.sha1(string_b + shared_secret_b)
    checksum = hb.hexdigest()

    return checksum


def add_checksum_to_url(url: str, shared_secret: str = None) -> str | None:
    """
    Добавляет параметр checksum в url, если параметр checksum есть в url,
    то он заменяется новым.
    :param url:
    :return:
    """

    if not url:
        return None

    if not shared_secret:
        raise Exception("shared_secret is None")

    split_url = urlsplit(url)
    api_call = split_url.path.split('/')[-1]

    parse_query = parse_qs(split_url.query)
    if parse_query.get("checksum"):
        del parse_query["checksum"]

    query = urlencode(parse_query, doseq=True)

    checksum = calculate_checksum(api_call + query, shared_secret)
    query_checksum = f"checksum={checksum}"

    if query:
        query_checksum = f"&{query_checksum}"

    checksum_url = f"{split_url.scheme}://{split_url.netloc}{split_url.path}?{query}{query_checksum}"

    return checksum_url
