
from django.conf import settings
from dynamic_preferences.serializers import BaseSerializer
from django.template import defaultfilters

from cryptography.fernet import Fernet


class EncryptedSerializer(BaseSerializer):

    @staticmethod
    def get_fernet():
        return Fernet(settings.FERNET_KEY)

    @classmethod
    def to_db(cls, value, **kwargs):

        value = cls.get_fernet().encrypt(value.encode()).decode()
        if not isinstance(value, str):
            raise cls.exception(
                "Cannot serialize, value {0} is not a string".format(value)
            )

        if kwargs.get("escape_html", False):
            return defaultfilters.force_escape(value)
        else:
            return value

    @classmethod
    def to_python(cls, value, **kwargs):
        """String deserialisation just return the value as a string"""

        if not value:
            return ""
        try:
            return str(value)
        except:
            pass
        try:
            return value.encode("utf-8")
        except:
            pass
        raise cls.exception("Cannot deserialize value {0} tostring".format(value))
