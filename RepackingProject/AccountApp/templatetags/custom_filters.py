import json

from django import template

register = template.Library()


@register.filter
def from_json(value):
    return json.loads(value)
