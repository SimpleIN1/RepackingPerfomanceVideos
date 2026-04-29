
from django import forms

from dynamic_preferences.preferences import Section
from dynamic_preferences.types import StringPreference, LongStringPreference
from dynamic_preferences.registries import global_preferences_registry

from core.dynamic_serializer import EncryptedSerializer


bbb_settings = Section("bbb_settings")
nextcloud_settings = Section("nextcloud_settings")

global_pref = global_preferences_registry.manager()


class CustomPreference(LongStringPreference):
    def get_field_kwargs(self):
        kwargs = super().get_field_kwargs()
        value = global_pref[f"{self.section}__{self.name}"]
        kwargs['help_text'] = f"Crypt value - {value[:10   ]}{'*'*15}"
        return kwargs


# BBB settings
@global_preferences_registry.register
class BBBSharedSecret(CustomPreference):
    section = bbb_settings
    name = "bbb_shared_secret"
    default = ""
    required = True

    serializer = EncryptedSerializer
    field_kwargs = {
        "widget": forms.PasswordInput()
    }


@global_preferences_registry.register
class BBBResource(StringPreference):
    section = bbb_settings
    name = "bbb_resource"
    default = ""
    required = True


@global_preferences_registry.register
class BBBURL(StringPreference):
    section = bbb_settings
    name = "bbb_url"
    default = ""
    required = True


# Nextcloud settings
@global_preferences_registry.register
class NextCloudResource(StringPreference):
    section = nextcloud_settings
    name = "nextcloud_resource"
    default = ""
    required = True


@global_preferences_registry.register
class NextCloudUser(StringPreference):
    section = nextcloud_settings
    name = "nextcloud_user"
    default = ""
    required = True


@global_preferences_registry.register
class NextCloudPassword(CustomPreference):
    section = nextcloud_settings
    name = "nextcloud_password"
    default = ""
    required = True

    serializer = EncryptedSerializer
    field_kwargs = {
        "widget": forms.PasswordInput()
    }


@global_preferences_registry.register
class NextCloudPath(StringPreference):
    section = nextcloud_settings
    name = "nextcloud_path"
    default = ""
    required = True


@global_preferences_registry.register
class NextCloudShareLink(StringPreference):
    section = nextcloud_settings
    name = "nextcloud_share_link"
    default = ""
    required = True


@global_preferences_registry.register
class NextCloudShareLinkPassword(CustomPreference):
    section = nextcloud_settings
    name = "nextcloud_share_link_password"
    default = ""
    required = True

    serializer = EncryptedSerializer
    field_kwargs = {
        "widget": forms.PasswordInput()
    }
