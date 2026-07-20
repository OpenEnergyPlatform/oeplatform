"""
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from pathlib import Path, PurePosixPath

import markdown2
from django import template
from django.contrib.staticfiles import finders
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="addclass")
def addclass(field, css):
    return field.as_widget(attrs={"class": css})


def _is_safe_static_path(filename):
    path = PurePosixPath(filename)
    return not path.is_absolute() and ".." not in path.parts


@register.simple_tag
def render_markdown(filename):
    """Find a markdown file in staticfiles and render it as HTML.

    The staticfiles lookup allows markdown content to live in any Django app's
    static directory. The fallback keeps the old ``base/static/content`` lookup
    behaviour for existing callers that pass only a filename.
    """
    if not _is_safe_static_path(filename):
        return ""

    md_path = finders.find(filename)
    if not md_path:
        md_path = (
            Path(__file__).resolve().parent.parent / "static" / "content" / filename
        )

    try:
        content = Path(md_path).read_text(encoding="utf-8")
    except OSError:
        return ""

    markdowner = markdown2.Markdown()
    return mark_safe(markdowner.convert(content))
