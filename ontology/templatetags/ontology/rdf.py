import re

from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter
def toHTML(jsn, optional_value=None):
    value = jsn.get("value")
    t = jsn.get("type")
    if t == "literal":
        return value
    elif t == "uri":
        return format_html('<a href="{0}">{1}</a>', value, optional_value or value)
    else:
        return value


@register.filter
def render_individual(jsn):
    subject = jsn["subject"]
    label = jsn.get("label", {}).get("value")
    re_last_resource = re.compile(r"\/([^\/]*)$")
    # If the ontology does not supply a label, take the leaf resource
    if label is None:
        match = re_last_resource.search(subject["value"])
        if match:
            label = match.groups()[0]
    return toHTML(subject, optional_value=label)
