# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from django import template

register = template.Library()


@register.filter(name="addclass")
def addclass(field, css):
    return field.as_widget(attrs={"class": css})
