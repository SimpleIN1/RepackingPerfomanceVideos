from datetime import datetime, timedelta, timezone

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.core.validators import (MinLengthValidator,
                                    MaxLengthValidator)


class UserModel(AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    username = models.CharField(verbose_name=_('Username'), max_length=150, default='', blank=True,)
    email = models.EmailField(unique=True)
    middle_name = models.CharField(max_length=150, null=True, blank=True, verbose_name="Отчество")
    two_factor_auth = models.BooleanField(default=False, verbose_name="Двухфакторная аутентификация (2FA)")
