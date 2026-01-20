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


def is_exist_dir(oc, remote_dir):
    try:
        rd = remote_dir
        if rd[0] != '/' and rd[-1] == '/':
            rd = '/'+remote_dir[:-1]
            remote_dir = f"/{remote_dir}"
        elif rd[0] == '/' and rd[-1] != '/':
            remote_dir = f"{remote_dir}/"
        elif rd[0] != '/' and rd[-1] != '/':
            remote_dir = f"/{remote_dir}/"
        else:
            rd = remote_dir[:-1]

        split_remote_dir, _ = os.path.split(rd)
        for item in oc.list(f"{split_remote_dir}"):
            if item.path == remote_dir:
                return True

    except owncloud.owncloud.HTTPResponseError:
        pass

    return False


def mkdir_parent(oc, remote_dir):
    dirname = ''
    dirs = remote_dir.split('/')
    for i in range(1, len(dirs)-1):
        dirname = os.path.join(dirname, dirs[i])

        if not is_exist_dir(oc, dirname):
            oc.mkdir(f"/{dirname}/")


def upload_to_nextcloud(oc, remote_file, local_source_file):
    remote_dir = os.path.dirname(remote_file)
    remote_dir_full = f"/{settings.NEXTCLOUD_PATH}/{remote_dir}/"
    remote_full = f"/{settings.NEXTCLOUD_PATH}/{remote_file}"

    if is_exist_dir(oc, f"{remote_full}/"):
        oc.delete(f"{remote_full}/")

    if remote_dir and not is_exist_dir(oc, remote_dir_full):
        mkdir_parent(oc, remote_dir_full)

    oc.put_file(remote_full, local_source_file, chunked=False)
