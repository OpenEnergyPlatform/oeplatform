"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The instance theming contract (#2637): what an instance replaces without a
fork, read where the platform renders it.

The brand is three templates under ``brand/``, so an instance overrides it from
a directory in ``INSTANCE_TEMPLATE_DIRS``: ``logo.html`` is markup and is
included; ``name.html`` and ``title_prefix.html`` are a line of text each,
read through ``brand_name`` and ``brand_title_prefix``, which strip the line
end a template file carries, so the text fits inside an attribute.
"""  # noqa: 501

from django import template
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

register = template.Library()


def _brand_text(name):
    # A template's text is markup its author wrote, so it is output as written,
    # as any template's is; strip() returns a plain str, which would be escaped.
    return mark_safe(render_to_string(f"brand/{name}.html").strip())


@register.simple_tag
def brand_name():
    """The platform's name, as ``brand/name.html`` gives it."""
    return _brand_text("name")


@register.simple_tag
def brand_title_prefix():
    """What every page title starts with, as ``brand/title_prefix.html`` gives it."""
    return _brand_text("title_prefix")


@register.simple_tag
def instance_stylesheets():
    """The static paths in ``INSTANCE_STYLESHEETS``, in order."""
    return settings.INSTANCE_STYLESHEETS
