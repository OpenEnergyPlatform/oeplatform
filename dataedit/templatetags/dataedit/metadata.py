# SPDX-FileCopyrightText: 2025 Martin Glauer <martinglauer89@gmail.com>
# SPDX-FileCopyrightText: 2025 Martin Glauer <martinglauer89@googlemail.com>
#
# SPDX-License-Identifier: MIT

from django import template

register = template.Library()


@register.filter
def is_dict(obj):
    return isinstance(obj, dict)
