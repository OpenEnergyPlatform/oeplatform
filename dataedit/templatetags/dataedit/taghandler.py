"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Tom Heimbrodt <https://github.com/tom-heimbrodt>
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import webcolors
from django import template

from dataedit.views import get_all_tags, get_popular_tags

register = template.Library()


@register.simple_tag
def get_tags(schema: str | None = None, table: str | None = None, limit=None):
    if limit:
        return get_popular_tags(table_name=table, limit=limit)
    else:
        return get_all_tags(table_name=table)


@register.simple_tag()
def readable_text_color(color_hex):
    r, g, b = webcolors.hex_to_rgb(color_hex)
    # Calculate brightness of the background and compare to threshold
    if 0.2126 * r + 0.7152 * g + 0.0722 * b < 0.279 * 255:
        return "#FFFFFF"
    else:
        return "#000000"


@register.simple_tag()
def format_bytes(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, "Yi", suffix)
