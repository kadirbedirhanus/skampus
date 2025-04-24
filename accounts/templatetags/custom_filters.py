# accounts/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_nested_item(dict_or_obj, key):
    if isinstance(dict_or_obj, dict):
        return dict_or_obj.get(key)
    return getattr(dict_or_obj, key, None)

@register.filter
def dict_key(d, key):
    return d.get(key, {})