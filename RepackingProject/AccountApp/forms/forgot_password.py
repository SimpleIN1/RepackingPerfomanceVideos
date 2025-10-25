
from django import forms
from django.conf import settings
from django.core.validators import MinLengthValidator, MaxLengthValidator

from AccountApp.forms.clean_password import PasswordCleaner
from AccountApp.services.user import get_user
from AccountApp.services.session_service import ConfirmationCodeSessionService, SessionService


class ForgotPasswordForm(forms.Form, SessionService):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "placeholder": "name@example.com"
        }),
    )

    def clean_email(self):
        data = self.cleaned_data["email"]
        self.user = get_user(email=data)

        if not self.user:
            self.add_error("email", "Такого email адреса не существует")

        return data


class ConfirmForgotPasswordForm(forms.Form, SessionService):
    kind_code = settings.KIND_CODE_FORGOT_PASSWORD

    code = forms.CharField(
        label="Код подтверждения",
        max_length=5,
        validators=[MinLengthValidator(5), MaxLengthValidator(5)],
        widget=forms.TextInput(attrs={
            "placeholder": "Введите 5-значный код"
        })
    )

    def clean_code(self):
        code = self.cleaned_data.get("code")

        ccm = ConfirmationCodeSessionService(self._session)

        if not ccm.check(code, self.kind_code):
            self.add_error("code", "Некорректный код или истек срок действия")
        else:
            ccm.confirm_code(self.kind_code)

        return code


class ChangePasswordForgotPasswordForm(PasswordCleaner, forms.Form):
    password = forms.CharField(
        label="Новый пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password",
            "placeholder": "Введите новый пароль"
        })
    )
    re_password = forms.CharField(
        label="Повторите новый пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password",
            "placeholder": "Повторите новый пароль"
        })
    )
