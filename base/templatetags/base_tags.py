"""
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import os

import markdown2
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="addclass")
def addclass(field, css):
    return field.as_widget(attrs={"class": css})


@register.simple_tag
def render_markdown(filename):
    """Read a markdown file from static/content/ and render it as HTML."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    md_path = os.path.join(base_dir, "static", "content", filename)
    try:
        with open(md_path, encoding="utf-8") as f:
            content = f.read()
        markdowner = markdown2.Markdown()
        return mark_safe(markdowner.convert(content))
    except FileNotFoundError:
        return ""
