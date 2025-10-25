import json
from datetime import datetime

from django.conf import settings
from django.urls import reverse_lazy
from django.middleware.csrf import get_token
from django.contrib.auth import login
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, Client, RequestFactory
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.middleware import SessionMiddleware

from AccountApp import forms
from AccountApp.models import UserModel
from AccountApp.views import LoginView
from AccountApp.services.user import get_user, update_user_by_pk, change_password_by_user_id_from_session


class RegisterUserTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_create_user(self):
        user_data = {
            "username": "user",
            "email": "user@mail.ru",
            "last_name": "last name user",
            "first_name": "first name user",
            "middle_name": "middle name user",
            "password": "passwoRd4_"
        }

        user = UserModel.objects.create_user(**user_data)
        self.assertTrue(user)

        created_user = UserModel.objects.get(email=user_data["email"])
        self.assertEqual(created_user, user)

    def test_form(self):
        user_data = {
            "email": "user@mail.ru",
            "last_name": "last name user",
            "first_name": "first name user",
            "middle_name": "middle name user",
            "password": "passwoRd4_",
            "re_password": "passwoRd4_",
        }

        form = forms.RegisterModelForm(data=user_data)
        self.assertTrue(form.is_valid())

        form.save()
        created_user = UserModel.objects.get(email=user_data["email"])
        self.assertTrue(created_user)
        self.assertFalse(created_user.is_active)

    def test_incorrect_form(self):
        user_data = {
            "email": "user@mail",
            "last_name": "last name user",
            "first_name": "first name user",
            "middle_name": "middle name user",
            "password": "passwo",
            "re_password": "passwoRd4_",
        }

        form = forms.RegisterModelForm(data=user_data)

        self.assertFalse(form.is_valid())

        self.assertTrue(form.errors)

        form_errors ={'email': ['Введите правильный адрес электронной почты.'],
                    'password': ['Введённый пароль слишком короткий. Он должен содержать как минимум 8 символов.']}
        self.assertEqual(dict(form.errors), form_errors)

    def test_incorrect_password_form(self):
        user_data = {
            "email": "user@mail.ru",
            "last_name": "last name user",
            "first_name": "first name user",
            "middle_name": "middle name user",
            "password": "passwoRd4_",
            "re_password": "passwoR1d4_",
        }

        form = forms.RegisterModelForm(user_data)

        self.assertFalse(form.is_valid())

        self.assertTrue(form.errors)

        form_errors = {'password': ['Пароли не равны'], 're_password': ['Пароли не равны']}
        self.assertEqual(dict(form.errors), form_errors)

    def test_get(self):
        response = self.client.get(reverse_lazy("register"))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        user_data = {
            "email": "user@mail.ru",
            "last_name": "last name user",
            "first_name": "first name user",
            "middle_name": "middle name user",
            "password": "passwoRd4_",
            "re_password": "passwoRd4_",
        }

        response = self.client.post(reverse_lazy("register"), data=user_data)
        self.assertEqual(response.status_code, 302)

        created_user = UserModel.objects.get(email=user_data["email"])

        self.assertTrue(created_user)
        self.assertFalse(created_user.is_active)

    def test_incorrect_post(self):
        user_data = {
            "email": "user@mail",
            "last_name": "last name user",
            "first_name": "first name user",
            "middle_name": "middle name user",
            "password": "passwo",
            "re_password": "passwoRd4_",
        }

        response = self.client.post(reverse_lazy("register"), data=user_data)
        self.assertEqual(response.status_code, 200)

        self.assertTrue(response.context)

        form_errors = {'email': ['Введите правильный адрес электронной почты.'],
                       'password': ['Введённый пароль слишком короткий. Он должен содержать как минимум 8 символов.']}
        self.assertTrue(response.context.get("form"))
        self.assertEqual(dict(response.context["form"].errors), form_errors)


class LoginUserTests(TestCase):
    def setUp(self):
        self.user_data = {
            "username": "user",
            "email": "user@mail.ru",
            "last_name": "last name user",
            "first_name": "first name user",
            "middle_name": "middle name user",
            "password": "passwoRd4_",
            "is_active": True,
        }
        self.user = UserModel.objects.create_user(**self.user_data)
        self.user_data_2fa = {
            "username": "user_2fa",
            "email": "user_2fa@mail.ru",
            "last_name": "last name user",
            "first_name": "first name user",
            "middle_name": "middle name user",
            "password": "passwoRd4_",
            "is_active": True,
            "two_factor_auth": True,
        }
        self.user_2fa = UserModel.objects.create_user(**self.user_data_2fa)
        self.client = Client()
        self.factory = RequestFactory()

    def test_login_user_post(self):
        data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }

        csrf_token = get_token(self.factory.get(reverse_lazy("login")))
        data["csrfmiddlewaretoken"] = csrf_token
        response = self.client.post(reverse_lazy("login"), data=data)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.user.two_factor_auth)

        location = response.headers.get("Location")
        self.assertTrue(location)
        self.assertEqual(location, str(reverse_lazy("repacking-records")))

    def test_login_user_post_2fa(self):
        data = {
            "email": self.user_data_2fa["email"],
            "password": self.user_data_2fa["password"]
        }

        csrf_token = get_token(self.factory.get(reverse_lazy("login")))
        data["csrfmiddlewaretoken"] = csrf_token
        response = self.client.post(reverse_lazy("login"), data=data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.user_2fa.two_factor_auth)

        location = response.headers.get("Location")
        self.assertTrue(location)
        self.assertEqual(location, str(reverse_lazy("login-2fa")))

    def test_login_user_post_incorrect_data(self):
        data = {
            "email": "asd@daf.ry",
            "password": "asdfs"
        }

        csrf_token = get_token(self.factory.get(reverse_lazy("login")))
        data["csrfmiddlewaretoken"] = csrf_token
        response = self.client.post(reverse_lazy("login"), data=data)

        self.assertEqual(response.status_code, 200)

        form_errors = {'__all__': ['Некорректный email или пароль']}
        self.assertEqual(dict(response.context["form"].errors), form_errors)


class Login2FAUserTests(TestCase):
    def setUp(self):
        settings.EMAIL_SENDER = False
        self.user_data_2fa = {
            "username": "user_2fa",
            "email": "user_2fa@mail.ru",
            "last_name": "last name user",
            "first_name": "first name user",
            "middle_name": "middle name user",
            "password": "passwoRd4_",
            "is_active": True,
            "two_factor_auth": True,
        }
        self.user_2fa = UserModel.objects.create_user(**self.user_data_2fa)
        self.client = Client()
        self.factory = RequestFactory()

    def test_login_2fa_user_post(self):
        s = SessionStore()
        s.create()
        code = "12345"
        s.update({
            settings.CONFIRMATION_CODE_SESSION: {
                settings.KIND_CODE_2FA: {
                    "code": code,
                    "confirmation_email": False,
                    "datetime_created": str(datetime.now().timestamp()).split('.')[0],
                    "user_id": self.user_2fa.id,
                    "data": {}
                }
            }
        })
        s.save()

        csrf_token = get_token(self.factory.get(reverse_lazy("login-2fa")))
        self.client.cookies.load({"sessionid": s.session_key})
        data = {
            "code": code,
            "csrfmiddlewaretoken": csrf_token
        }
        response = self.client.post(reverse_lazy("login-2fa"), data=data)
        self.assertEqual(response.status_code, 302)

        location = response.headers.get("Location")
        self.assertTrue(location)
        self.assertEqual(location, str(reverse_lazy("repacking-records")))

    def test_login_2fa_user_post_not_session_user_id(self):
        s = SessionStore()
        s.create()
        code = "12345"
        s.update({
            settings.CONFIRMATION_CODE_SESSION: {
                settings.KIND_CODE_2FA: {
                    "code": code,
                    "confirmation_email": False,
                    "datetime_created": str(datetime.now().timestamp()).split('.')[0],
                    "user_id": None,
                    "data": {}
                }
            }
        })
        s.save()

        csrf_token = get_token(self.factory.get(reverse_lazy("login-2fa")))
        self.client.cookies.load({"sessionid": s.session_key})
        data = {
            "code": code,
            "csrfmiddlewaretoken": csrf_token
        }
        response = self.client.post(reverse_lazy("login-2fa"), data=data)
        self.assertEqual(response.status_code, 302)

        location = response.headers.get("Location")
        self.assertTrue(location)
        self.assertEqual(location, str(reverse_lazy("login")))


class ForgotPasswordTests(TestCase):
    def setUp(self):
        self.user_data = {
            "username": "user",
            "email": "user@mail.ru",
            "last_name": "last name user",
            "first_name": "first name user",
            "middle_name": "middle name user",
            "password": "passwoRd4_",
            "is_active": True,
        }
        self.user = UserModel.objects.create_user(**self.user_data)
        self.client = Client()
        self.factory = RequestFactory()

    def test_forgot_password_post(self):
        data = {
            "email": self.user_data["email"]
        }

        csrf_token = get_token(self.factory.get(reverse_lazy("forgot-password")))
        data["csrfmiddlewaretoken"] = csrf_token

        response = self.client.post(reverse_lazy("forgot-password"), data=data)
        self.assertEqual(response.status_code, 302)

        location = response.headers.get("Location")
        self.assertTrue(location)
        self.assertEqual(location, str(reverse_lazy("confirm-forgot-password")))

    def test_forgot_password_post_not_found_email(self):
        data = {
            "email": "user1@mail.ru"
        }

        csrf_token = get_token(self.factory.get(reverse_lazy("forgot-password")))
        data["csrfmiddlewaretoken"] = csrf_token

        response = self.client.post(reverse_lazy("forgot-password"), data=data)
        self.assertEqual(response.status_code, 200)

        form_errors = {'email': ['Такого email адреса не существует']}
        self.assertEqual(dict(response.context["form"].errors), form_errors)

    def test_confirm_forgot_password_post(self):

        s = SessionStore()
        s.create()
        code = "12345"
        s.update({
            settings.CONFIRMATION_CODE_SESSION: {
                settings.KIND_CODE_FORGOT_PASSWORD: {
                    "code": code,
                    "confirmation_email": False,
                    "datetime_created": str(datetime.now().timestamp()).split('.')[0],
                    "user_id": self.user.id,
                    "data": {}
                }
            }
        })
        s.save()

        data = {
            "code": code
        }
        self.client.cookies.load({"sessionid": s.session_key})
        csrf_token = get_token(self.factory.get(reverse_lazy("confirm-forgot-password")))
        data["csrfmiddlewaretoken"] = csrf_token

        response = self.client.post(reverse_lazy("confirm-forgot-password"), data=data)
        self.assertEqual(response.status_code, 302)

        location = response.headers.get("Location")
        self.assertTrue(location)
        self.assertEqual(location, str(reverse_lazy("change-forgot-password")))

    def test_confirm_forgot_password_post_incorrect_session(self):

        s = SessionStore()
        s.create()
        code = "12345"
        s.update({
            settings.CONFIRMATION_CODE_SESSION: {
                settings.KIND_CODE_FORGOT_PASSWORD: {
                    "code": code,
                }
            }
        })
        s.save()

        data = {
            "code": code
        }
        self.client.cookies.load({"sessionid": s.session_key})
        csrf_token = get_token(self.factory.get(reverse_lazy("confirm-forgot-password")))
        data["csrfmiddlewaretoken"] = csrf_token

        response = self.client.post(reverse_lazy("confirm-forgot-password"), data=data)
        self.assertEqual(response.status_code, 200)

        form_errors = {"code": ["Некорректный код или истек срок действия"]}
        self.assertEqual(dict(response.context["form"].errors), form_errors)

    def test_change_forgot_password_post(self):
        s = SessionStore()
        s.create()
        code = "12345"
        s.update({
            settings.CONFIRMATION_CODE_SESSION: {
                settings.KIND_CODE_FORGOT_PASSWORD: {
                    "code": code,
                    "confirmation_email": True,
                    "datetime_created": str(datetime.now().timestamp()).split('.')[0],
                    "user_id": self.user.id,
                    "data": {}
                }
            }
        })
        s.save()

        data = {
            "password": "PassworD1_",
            "re_password": "PassworD1_"
        }
        self.client.cookies.load({"sessionid": s.session_key})
        csrf_token = get_token(self.factory.get(reverse_lazy("change-forgot-password")))
        data["csrfmiddlewaretoken"] = csrf_token

        response = self.client.post(reverse_lazy("change-forgot-password"), data=data)

        self.assertEqual(response.status_code, 302)

        location = response.headers.get("Location")
        self.assertTrue(location)
        self.assertEqual(location, str(reverse_lazy("login")))

    def test_change_forgot_password_post_not_equal_passwords(self):
        s = SessionStore()
        s.create()
        code = "12345"
        s.update({
            settings.CONFIRMATION_CODE_SESSION: {
                settings.KIND_CODE_FORGOT_PASSWORD: {
                    "code": code,
                    "confirmation_email": True,
                    "datetime_created": str(datetime.now().timestamp()).split('.')[0],
                    "user_id": self.user.id,
                    "data": {}
                }
            }
        })
        s.save()

        data = {
            "password": "PassworD1_",
            "re_password": "PassworD1_1"
        }
        self.client.cookies.load({"sessionid": s.session_key})
        csrf_token = get_token(self.factory.get(reverse_lazy("change-forgot-password")))
        data["csrfmiddlewaretoken"] = csrf_token

        response = self.client.post(reverse_lazy("change-forgot-password"), data=data)
        self.assertEqual(response.status_code, 200)

        form_errors = {'password': ['Пароли не равны'], 're_password': ['Пароли не равны']}
        self.assertEqual(dict(response.context["form"].errors), form_errors)


class ProfileTests(TestCase):
    def setUp(self):
        self.user_data = {
            "username": "user",
            "email": "user@mail.ru",
            "last_name": "last name user",
            "first_name": "first name user",
            "middle_name": "middle name user",
            "password": "passwoRd4_",
            "is_active": True,
        }
        self.user = UserModel.objects.create_user(**self.user_data)

        self.user_data2 = {
            "username": "user2",
            "email": "user2@mail.ru",
            "last_name": "last name user2",
            "first_name": "first name user2",
            "middle_name": "middle name user2",
            "password": "passwoRd4_2",
            "is_active": True,
        }
        self.user2 = UserModel.objects.create_user(**self.user_data2)

        self.client = Client()
        self.factory = RequestFactory()

    def _add_session_to_request(self, request):
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

    def test_base_info_post_current_email(self):

        data = {
            "email": "user@mail.ru",
            "last_name": "last name user1",
            "first_name": "first name user1",
            "middle_name": "middle name user1",
        }
        dummy_request = self.factory.get(reverse_lazy("profile"))

        self._add_session_to_request(dummy_request)
        dummy_request.user = self.user
        login(dummy_request, self.user)
        dummy_request.session.save()

        csrf_token = get_token(dummy_request)
        data["csrfmiddlewaretoken"] = csrf_token

        self.client.cookies.load({"sessionid":  dummy_request.session.session_key})
        response = self.client.post(reverse_lazy("base-info-profile"), data=data)

        self.assertEqual(response.status_code, 200)

        response_data = {"success": True}
        self.assertEqual(json.loads(response.content.decode()), response_data)

        user = UserModel.objects.get(email=self.user.email)
        saved_data = {
            "email": user.email,
            "last_name": user.last_name,
            "first_name": user.first_name,
            "middle_name": user.middle_name
        }
        del data["csrfmiddlewaretoken"]
        self.assertEqual(saved_data, data)

    def test_base_info_post_unique_email(self):

        data = {
            "email": "user2@mail.ru",
            "last_name": "last name user2",
            "first_name": "first name user2",
            "middle_name": "middle name user2",
        }
        dummy_request = self.factory.get(reverse_lazy("profile"))

        self._add_session_to_request(dummy_request)
        dummy_request.user = self.user
        login(dummy_request, self.user)
        dummy_request.session.save()

        csrf_token = get_token(dummy_request)
        data["csrfmiddlewaretoken"] = csrf_token

        self.client.cookies.load({"sessionid":  dummy_request.session.session_key})
        response = self.client.post(reverse_lazy("base-info-profile"), data=data)

        self.assertEqual(response.status_code, 400)

        response_data = {"success": False,
                         "fields": {"email": ["Пользователь с таким email адресом уже существует"]}}
        self.assertEqual(json.loads(response.content.decode()), response_data)

    def test_base_info_post_other_email(self):

        data = {
            "email": "user3@mail.ru",
            "last_name": "last name user1",
            "first_name": "first name user1",
            "middle_name": "middle name user1",
        }
        dummy_request = self.factory.get(reverse_lazy("profile"))

        self._add_session_to_request(dummy_request)
        dummy_request.user = self.user
        login(dummy_request, self.user)
        dummy_request.session.save()

        csrf_token = get_token(dummy_request)
        data["csrfmiddlewaretoken"] = csrf_token

        self.client.cookies.load({"sessionid":  dummy_request.session.session_key})
        response = self.client.post(reverse_lazy("base-info-profile"), data=data)

        self.assertEqual(response.status_code, 200)

        response_data = {"success": True, "redirect": str(reverse_lazy("confirm-email-profile"))}
        self.assertEqual(json.loads(response.content.decode()), response_data)

    def test_change_password_profile_post(self):
        data = {
            "current_password": self.user_data["password"],
            "password": "qwerty12_1Da",
            "re_password": "qwerty12_1Da",
        }
        dummy_request = self.factory.get(reverse_lazy("profile"))

        self._add_session_to_request(dummy_request)
        dummy_request.user = self.user
        login(dummy_request, self.user)
        dummy_request.session.save()

        csrf_token = get_token(dummy_request)
        data["csrfmiddlewaretoken"] = csrf_token

        self.client.cookies.load({"sessionid":  dummy_request.session.session_key})
        response = self.client.post(reverse_lazy("change-password-profile"), data=data)

        self.assertEqual(response.status_code, 200)

        response_data = {"success": True}
        self.assertEqual(json.loads(response.content.decode()), response_data)

        user = UserModel.objects.get(email=self.user.email)
        self.assertTrue(user.check_password(data["password"]))

    def test_change_password_profile_post_incorrect_data(self):
        data = {
            "current_password": "Dasddd=dd---",  # Incorrect
            "password": "qwerty12_1Da",          # Incorrect
            "re_password": "qwerty12_1Da12",     # Incorrect
        }
        dummy_request = self.factory.get(reverse_lazy("profile"))

        self._add_session_to_request(dummy_request)
        dummy_request.user = self.user
        login(dummy_request, self.user)
        dummy_request.session.save()

        csrf_token = get_token(dummy_request)
        data["csrfmiddlewaretoken"] = csrf_token

        self.client.cookies.load({"sessionid":  dummy_request.session.session_key})
        response = self.client.post(reverse_lazy("change-password-profile"), data=data)

        self.assertEqual(response.status_code, 400)

        response_data = {'fields': {'current_password': ['Текущий пароль не прошел проверку'],
             'password': ['Новый и повторный пароли должны сопадать'],
             're_password': ['Новый и повторный пароли должны сопадать']},
             'success': False}
        self.assertEqual(json.loads(response.content.decode()), response_data)

    def test_security_profile_post(self):
        data = {
            "two_factor_auth": True
        }
        dummy_request = self.factory.get(reverse_lazy("profile"))

        self._add_session_to_request(dummy_request)
        dummy_request.user = self.user
        login(dummy_request, self.user)
        dummy_request.session.save()

        csrf_token = get_token(dummy_request)
        data["csrfmiddlewaretoken"] = csrf_token

        self.client.cookies.load({"sessionid":  dummy_request.session.session_key})
        response = self.client.post(reverse_lazy("security-profile"), data=data)

        self.assertEqual(response.status_code, 200)

        response_data = {'success': True}
        self.assertEqual(json.loads(response.content.decode()), response_data)


class ConfirmEmailProfileTests(TestCase):
    def setUp(self):
        self.user_data = {
            "username": "user",
            "email": "user@mail.ru",
            "last_name": "last name user",
            "first_name": "first name user",
            "middle_name": "middle name user",
            "password": "passwoRd4_",
            "is_active": True,
        }
        self.user = UserModel.objects.create_user(**self.user_data)

        self.client = Client()
        self.factory = RequestFactory()

    def _add_session_to_request(self, request):
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

    def test_confirm_email_post(self):
        dummy_request = self.factory.get(reverse_lazy("profile"))
        self._add_session_to_request(dummy_request)
        dummy_request.user = self.user
        login(dummy_request, self.user)

        code = "12345"
        email = "user12@mail.ru"

        dummy_request.session[settings.CONFIRMATION_CODE_SESSION] = {
            settings.KIND_CODE_EMAIL: {
                "code": code,
                "confirmation_email": False,
                "datetime_created": str(datetime.now().timestamp()).split('.')[0],
                "user_id": self.user.id,
                "data": {"email": email}
            }
        }
        dummy_request.session.save()

        data = {
            "code": code
        }
        self.client.cookies.load({"sessionid": dummy_request.session.session_key})

        csrf_token = get_token(dummy_request)
        data["csrfmiddlewaretoken"] = csrf_token

        response = self.client.post(reverse_lazy("confirm-email-profile"), data=data)
        self.assertEqual(response.status_code, 302)

        location = response.headers.get("Location")
        self.assertTrue(location)
        self.assertEqual(location, str(reverse_lazy("profile")))

        user = UserModel.objects.get(email=email)
        self.assertTrue(user)


class UserServiceTests(TestCase):
    def setUp(self):
        self.user_data = {
            "username": "user",
            "email": "user@mail.ru",
            "last_name": "last name user",
            "first_name": "first name user",
            "password": "passwoRd4_",
        }
        self.user = UserModel.objects.create_user(**self.user_data)

    def test_get_user(self):
        user = get_user(email=self.user_data["email"])

        self.assertTrue(user)
        self.assertEqual(user.email, self.user_data["email"])

    def test_get_user_not_found(self):
        user = get_user(email="asd@das.rrt")

        self.assertFalse(user)

    def test_update_user(self):
        data = {
            "username": "user1",
            "email": "user1@mail.ru",
            "last_name": "last name user1",
            "first_name": "first name user1",
            "middle_name": "middle name user1",
            "is_active": True,
        }
        update_user_by_pk(pk=1, **data)
        updated_user = UserModel.objects.get(pk=1)
        updated_data = {
            "username": updated_user.username,
            "last_name": updated_user.last_name,
            "first_name": updated_user.first_name,
            "middle_name": updated_user.middle_name,
            "is_active": updated_user.is_active,
            "email": updated_user.email
        }
        self.assertEqual(updated_data, data)

    def test_change_user_password(self):
        """
        # create session
        # create user
        # update session
        # execute func
        # another checkes

        :return:
        """

        s = SessionStore()
        s.create()
        code = "12345"
        s.update({
            settings.CONFIRMATION_CODE_SESSION: {
                settings.KIND_CODE_FORGOT_PASSWORD: {
                    "code": code,
                    "confirmation_email": True,
                    "datetime_created": str(datetime.now().timestamp()).split('.')[0],
                    "user_id": self.user.id,
                    "data": {}
                }
            }
        })
        s.save()

        password = "qwerty12D_"
        res = change_password_by_user_id_from_session(password, s)
        self.assertTrue(res)

        user = UserModel.objects.get(pk=res)
        self.assertTrue(user.check_password(password))

    def test_change_user_password_not_confirm(self):

        s = SessionStore()
        s.create()
        code = "12345"
        s.update({
            settings.CONFIRMATION_CODE_SESSION: {
                settings.KIND_CODE_FORGOT_PASSWORD: {
                    "code": code,
                    "confirmation_email": False,
                    "datetime_created": str(datetime.now().timestamp()).split('.')[0],
                    "user_id": self.user.id,
                    "data": {}
                }
            }
        })
        s.save()

        password = "qwerty12D_"
        res = change_password_by_user_id_from_session(password, s)
        self.assertFalse(res)


class SessionServiceTests(TestCase):
    pass
