from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def empty(dictionary):

    bool1 = dictionary is None
    bool2 = dictionary is False
    bool3 = len(dictionary) == 0

    return bool1 or bool2 or bool3
