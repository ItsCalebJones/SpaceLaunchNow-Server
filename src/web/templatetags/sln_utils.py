# app/templatetags/sln_utils.py
from api.models import Events, Launch
from django import template

register = template.Library()


@register.filter
def get_type(value):
    if isinstance(value, Events):
        return "event"
    elif isinstance(value, Launch):
        return "launch"
    else:
        return None
