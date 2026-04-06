import hmac
import hashlib
import jwt

from django.conf import settings
from rest_framework.permissions import BasePermission


class SecureSignaturePermission(BasePermission):
    def has_permission(self, request, view):
        auth = request.headers.get('Authorization')
        auth_split = auth.split(' ')

        if not len(auth_split) == 2:
            return False

        token = auth_split[1]
        try:
            jwt.decode(token, settings.BBB_SHARED_SECRET, algorithms="HS512")
        except (jwt.InvalidSignatureError, jwt.ExpiredSignatureError, jwt.DecodeError):
            return False

        return True
