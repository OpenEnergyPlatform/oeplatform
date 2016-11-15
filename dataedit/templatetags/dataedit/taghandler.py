from django import template
from dataedit import models
import webcolors
from dataedit.views import get_all_tags
register = template.Library()


@register.assignment_tag
def get_tags(schema=None, table=None, limit=None):
    if limit:
        return get_all_tags(schema=schema, table=table)[:limit]
    else:
        return get_all_tags(schema=schema, table=table)

@register.simple_tag()
def readable_text_color(color_hex):
    r, g, b = webcolors.hex_to_rgb(color_hex)
    # Calculate brightness of the background and compare to threshold
    if 0.2126 * r + 0.7152 * g+ 0.0722 * b < 0.279*255:
        return "#FFFFFF"
    else:
        return "#000000"
