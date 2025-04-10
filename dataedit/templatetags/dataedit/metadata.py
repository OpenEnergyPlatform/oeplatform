# SPDX-FileCopyrightText: 2025 MGlauer <martinglauer89@gmail.com>
# SPDX-FileCopyrightText: 2025 MGlauer <martinglauer89@googlemail.com>
#
# SPDX-License-Identifier: MIT

from django import template

register = template.Library()


@register.filter
def is_dict(obj):
    return isinstance(obj, dict)
