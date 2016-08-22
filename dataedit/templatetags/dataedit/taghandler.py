from django import template
from dataedit import models
import webcolors

register = template.Library()


@register.assignment_tag
def get_tags():
    return models.Tag.objects.all()[:10]

@register.simple_tag()
def readable_text_color(color_hex):
    r,g,b = webcolors.hex_to_rgb(color_hex)
    L = 0.2126 * r + 0.7152 * g+ 0.0722 * b
    print((r,g,b), L, 0.279*255)
    if L < 0.279*255:
        return "#FFFFFF"
    else:
        return "#000000"