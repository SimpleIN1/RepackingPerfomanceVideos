
from django import forms
from django.conf import settings
from django.db import transaction
from django.core.validators import MinLengthValidator, MaxLengthValidator

from AccountApp.services.user import get_user
from AccountApp.services.session_service import ConfirmationCodeSessionService, SessionService


class ConfirmEmailForm(forms.Form, SessionService):
    kind_code = settings.KIND_CODE_EMAIL

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

    def save(self, us):
        ccm = ConfirmationCodeSessionService(us.session)
        data = ccm.get_data(self.kind_code)

        if data:
            with transaction.atomic():
                us.user.email = data["email"]
                us.user.save()
