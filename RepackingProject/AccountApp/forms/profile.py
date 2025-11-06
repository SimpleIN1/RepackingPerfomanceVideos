
from django import forms
from django.contrib.auth.password_validation import validate_password

from AccountApp.models import UserModel
from AccountApp.services.user import get_user, update_user_by_pk


class BaseInfoProfileGETForm(forms.Form):
    fields = ['last_name', 'middle_name', 'first_name', 'email']
    last_name = forms.CharField(
        max_length=150,
        label="Фамилия",
        widget=forms.TextInput(attrs={
            "placeholder": "Ваша фамилия"
        })
    )
    first_name = forms.CharField(
        max_length=150,
        label="Имя",
        widget=forms.TextInput(attrs={
            "placeholder": "Ваша имя"
        })
    )
    middle_name = forms.CharField(
        max_length=150,
        label="Отчество",
        widget=forms.TextInput(attrs={
            "placeholder": "Ваша отчество"
        }),
        required=False
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "placeholder": "name@example.com"
        }),
    )


class BaseInfoProfilePOSTForm(BaseInfoProfileGETForm):
    _current_user = None

    def set_current_user(self, user):
        self.current_user = user

    def clean_email(self):
        email = self.cleaned_data["email"]

        user = get_user(email=email)

        if user and user.email != self.current_user.email:
            self.add_error("email", "Пользователь с таким email адресом уже существует")

        return email

    def save(self, user):
        user.last_name = self.cleaned_data["last_name"]
        user.first_name = self.cleaned_data["first_name"]
        user.middle_name = self.cleaned_data["middle_name"]
        user.save()


class ChangePasswordProfileForm(forms.Form):
    current_password = forms.CharField(
        label="Текущий пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password",
            "placeholder": "Введите текущий пароль"
        })
    )
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
        }),
        required=False
    )

    def set_user(self, user):
        self.user = user

    def clean_password(self):
        password = self.cleaned_data["password"]
        current_password = self.cleaned_data["current_password"]

        if not self.user.check_password(current_password):
            self.add_error("current_password", "Текущий пароль не прошел проверку")

        validate_password(password, user=UserModel)

        if current_password == password:
            self.add_error("password", "Пароли не должны сопадать")
            self.add_error("current_password", "Пароли не должны сопадать")

        return password

    def clean_re_password(self):
        re_password = self.cleaned_data["re_password"]
        password = self.cleaned_data["password"]

        if re_password != password:
            self.add_error("password", "Новый и повторный пароли должны сопадать")
            self.add_error("re_password", "Новый и повторный пароли должны сопадать")

        return re_password

    def save(self, user):
        user.set_password(self.cleaned_data["password"])
        user.save()


class SecurityProfileForm(forms.Form):
    fields = ["two_factor_auth"]
    two_factor_auth = forms.BooleanField(
        label="Двухфакторная аутентификация (2FA)",
        widget=forms.CheckboxInput(attrs={}),
        required=False
    )

    def save(self, user):
        user.two_factor_auth = self.cleaned_data["two_factor_auth"]
        user.save()
