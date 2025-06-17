# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
#
# SPDX-License-Identifier: MIT

from django import template

register = template.Library()


@register.filter
def is_dict(obj):
    return isinstance(obj, dict)
