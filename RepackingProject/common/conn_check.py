import requests
from requests.exceptions import ConnectTimeout


def health_check(domain: str, schema: str = "https") -> bool:
    url = f"{schema}://{domain}"
    try:
        r = requests.get(url, timeout=2)
        return True
    except ConnectTimeout:
        return False
