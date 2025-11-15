from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.validators import MinLengthValidator, MaxLengthValidator

from AccountApp.services.session_service import ConfirmationCodeSessionService, SessionService


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "placeholder": "name@example.com"
        }),
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password",
            "placeholder": "Введите пароль"
        })
    )


class Login2FAForm(forms.Form, SessionService):
    _session = None
    _user_id = None

    code = forms.CharField(
        label="Код подтверждения",
        max_length=5,
        validators=[MinLengthValidator(5), MaxLengthValidator(5)],
        widget=forms.TextInput(attrs={
            "placeholder": "Введите 5-значный код"
        })
    )

    def get_user_id(self):
        return self._user_id

    def clean_code(self):
        code = self.cleaned_data["code"]

        ccs = ConfirmationCodeSessionService(self._session)

        if not ccs.check_kind(settings.KIND_CODE_2FA):
            self.add_error("code", "Некорректный код или истек срок действия")
            return code

        ccs.increase_attempt(settings.KIND_CODE_2FA)

        attempt = ccs.get_attempt(settings.KIND_CODE_2FA)
        check = ccs.check(code, settings.KIND_CODE_2FA)

        if attempt >= settings.SUCCESS_ATTEMPT_COUNT and not check:
            self.add_error("code", "Количество успешных попыток ввода закончилось. Выполните повторный вход")
        elif not check:
            self.add_error(
                "code",
                f"Некорректный код или истек срок действия. Осталось попыток: {settings.SUCCESS_ATTEMPT_COUNT - attempt}"
            )

        self._user_id = ccs.get_user_id(settings.KIND_CODE_2FA)

        return code