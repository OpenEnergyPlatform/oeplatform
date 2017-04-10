from django import template
register = template.Library()

@register.filter
def is_dict(obj):
    return isinstance(obj,dict)