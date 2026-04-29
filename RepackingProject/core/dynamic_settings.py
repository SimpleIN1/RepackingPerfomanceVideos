import sys

from dynamic_preferences.registries import global_preferences_registry

from core.dynamic_serializer import EncryptedSerializer


if "migrate" not in sys.argv:
    global_pref = global_preferences_registry.manager()

    fernet = EncryptedSerializer().get_fernet()

    BBB_SHARED_SECRET = str(fernet.decrypt(global_pref["bbb_settings__bbb_shared_secret"]))
    BBB_RESOURCE = global_pref["bbb_settings__bbb_resource"]
    BBB_URL = global_pref["bbb_settings__bbb_url"]

    NEXTCLOUD_RESOURCE = global_pref["nextcloud_settings__nextcloud_resource"]
    NEXTCLOUD_USER = global_pref["nextcloud_settings__nextcloud_user"]
    NEXTCLOUD_PASSWORD = str(fernet.decrypt(global_pref["nextcloud_settings__nextcloud_password"]))
    NEXTCLOUD_PATH = global_pref["nextcloud_settings__nextcloud_path"]
    NEXTCLOUD_SHARE_LINK = global_pref["nextcloud_settings__nextcloud_share_link"]
    NEXTCLOUD_SHARE_LINK_PASSWORD = str(fernet.decrypt(global_pref["nextcloud_settings__nextcloud_share_link_password"]))
