import jwt

from core import dynamic_settings
from rest_framework.permissions import BasePermission


class SecureSignaturePermission(BasePermission):
    def has_permission(self, request, view):
        auth = request.headers.get('Authorization')
        if not auth:
            return False

        auth_split = auth.split(' ')

        if not len(auth_split) == 2:
            return False

        token = auth_split[1]
        try:
            jwt.decode(token, dynamic_settings.BBB_SHARED_SECRET, algorithms="HS512")
        except (jwt.InvalidSignatureError, jwt.ExpiredSignatureError, jwt.DecodeError):
            return False

        return True
