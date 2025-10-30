from django import forms

from RepackingApp.validators import validate_recording_ids


class ProcessRecordingsForm(forms.Form):
    recording_ids = forms.CharField(
        widget=forms.Textarea,
        validators=[validate_recording_ids]
    )
