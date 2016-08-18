from django import template
from dataedit import models

register = template.Library()


@register.assignment_tag
def get_tags():
    return models.Tag.objects.all()[:10]