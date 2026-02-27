from django import template
import os

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def basename(value):
    """Get the filename from a path"""
    if not value:
        return ""
    return os.path.basename(str(value))

@register.filter
def split(value, arg):
    """Split a string by the given argument"""
    if value is None:
        return []
    return value.split(arg)
