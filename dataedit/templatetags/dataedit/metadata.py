# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer>
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer>
#
# SPDX-License-Identifier: MIT

from django import template

register = template.Library()


@register.filter
def is_dict(obj):
    return isinstance(obj, dict)
