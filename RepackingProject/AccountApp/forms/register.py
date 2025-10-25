
from django import forms

from AccountApp.models import UserModel
from AccountApp.forms.clean_password import PasswordCleaner


class RegisterModelForm(PasswordCleaner, forms.ModelForm):
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
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password",
            "placeholder": "Введите пароль"
        })
    )
    re_password = forms.CharField(
        label="Повторите пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password",
            "placeholder": "Повторите пароль"
        })
    )

    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.is_active = False

        if commit:
            instance.save()

        return instance

    class Meta:
        model = UserModel
        fields = ['last_name', 'middle_name', 'first_name', 'email', 'password', 're_password']
