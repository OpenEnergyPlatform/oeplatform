# SPDX-FileCopyrightText: 2018 Martin Glauer <MGlauer>
# SPDX-FileCopyrightText: oeplatform <https://github.com/OpenEnergyPlatform/oeplatform/>
# SPDX-License-Identifier: MIT

from django import template

register = template.Library()


@register.filter(name="addclass")
def addclass(field, css):
    return field.as_widget(attrs={"class": css})
