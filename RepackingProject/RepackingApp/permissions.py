import jwt

from rest_framework.permissions import BasePermission
from dynamic_preferences.registries import global_preferences_registry

from core.dynamic_serializer import EncryptedSerializer
from core.dynamic_settings import global_pref


class SecureSignaturePermission(BasePermission):
    def has_permission(self, request, view):

        fernet = EncryptedSerializer().get_fernet()
        BBB_SHARED_SECRET = str(fernet.decrypt(global_pref["bbb_settings__bbb_shared_secret"]).decode())

        auth = request.headers.get('Authorization')
        if not auth:
            return False

        auth_split = auth.split(' ')

        if not len(auth_split) == 2:
            return False

        token = auth_split[1]
        try:
            jwt.decode(token, BBB_SHARED_SECRET, algorithms="HS512")
        except (jwt.InvalidSignatureError, jwt.ExpiredSignatureError, jwt.DecodeError):
            return False

        return True
