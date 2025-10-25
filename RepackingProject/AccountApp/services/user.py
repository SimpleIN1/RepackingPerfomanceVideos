from django.conf import settings
from django.db import transaction
from django.contrib.auth.hashers import make_password

from AccountApp.models import UserModel
from AccountApp.services.session_service import ConfirmationCodeSessionService


def get_user(**kwargs):
    """
    Запрос в базу данных данных о пользователе, используя параметры kwargs
    :param kwargs:
    :return:
    """

    try:
        user = UserModel.objects.get(**kwargs)
    except UserModel.DoesNotExist:
        user = None

    return user


def update_user_by_pk(pk, **kwargs):
    """
    Обновление информации пользователя по его id
    :param pk:
    :param kwargs:
    :return:
    """

    with transaction.atomic():
        UserModel.objects.filter(pk=pk).update(**kwargs)


def change_password_by_user_id_from_session(password, session):
    """
    Изменение пароля пользователя с проверкой подтверждения
    :param password:
    :param session:
    :return:
    """

    ccs = ConfirmationCodeSessionService(session)

    if not ccs.check_confirm(settings.KIND_CODE_FORGOT_PASSWORD):
        return None

    user_id = ccs.get_user_id(settings.KIND_CODE_FORGOT_PASSWORD)
    ccs.clear_kind(settings.KIND_CODE_FORGOT_PASSWORD)

    password_salt = make_password(password)
    update_user_by_pk(pk=user_id, password=password_salt)
    return user_id
