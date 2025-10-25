from django import forms


class ProcessRecordingsForm(forms.Form):
    recording_ids = forms.CharField(
        widget=forms.Textarea
    )
