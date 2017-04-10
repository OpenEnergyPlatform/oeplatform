from django import template
register = template.Library()

@register.simple_tag()
def obj2js(obj):
    return obj.__dict__()