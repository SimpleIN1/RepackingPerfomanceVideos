import re

from django.core.exceptions import ValidationError


pattern = r'^\w{40}\-\d{13}$'
pattern_compile = re.compile(pattern)


def validate_recording_id(value):
    if not pattern_compile.search(value):
        raise ValidationError("RIDs не соответствуют шаблону.")


def validate_recording_ids(value):
    items = value.split(',')
    for item in items:
        validate_recording_id(item)
