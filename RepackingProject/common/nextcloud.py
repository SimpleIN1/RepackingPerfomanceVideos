import os.path

import owncloud
from django.conf import settings


def set_up():
    oc = owncloud.Client(f'https://{settings.NEXTCLOUD_RESOURCE}')
    oc.login(settings.NEXTCLOUD_USER, settings.NEXTCLOUD_PASSWORD)
    return oc


def mkdir_root(oc):
    for item in oc.list("/"):
        if item.path == f"/{settings.NEXTCLOUD_PATH}/":
            break
    else:
        oc.mkdir(settings.NEXTCLOUD_PATH)


oc = set_up()
mkdir_root(oc)


def is_exist_dir(remote_dir):
    for item in oc.list(f"/{settings.NEXTCLOUD_PATH}/"):
        if item.path == f"/{settings.NEXTCLOUD_PATH}/{remote_dir}/":
            return True
    return False


def upload_to_nextcloud(remote_file, local_source_file):
    remote_dir = os.path.dirname(remote_file)
    remote_dir_full = f"/{settings.NEXTCLOUD_PATH}/{remote_dir}"
    remote_full = f"/{settings.NEXTCLOUD_PATH}/{remote_file}"

    if is_exist_dir(f"{remote_full}/"):
        oc.delete(f"{remote_full}/")

    if remote_dir and not is_exist_dir(remote_dir):
        oc.mkdir(remote_dir_full)

    oc.put_file(remote_full, local_source_file)
