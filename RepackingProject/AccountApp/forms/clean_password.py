from django import forms
from django.contrib.auth.password_validation import validate_password

from AccountApp.models import UserModel


class PasswordCleaner(forms.Form):
    def clean_password(self):
        data = self.cleaned_data["password"]
        validate_password(data, user=UserModel)
        return data

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        re_password = cleaned_data.get("re_password")

        if password and re_password and password != re_password:
            self.add_error("password", "Пароли не равны")
            self.add_error("re_password", "Пароли не равны")

        return cleaned_data
