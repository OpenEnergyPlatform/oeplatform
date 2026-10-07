"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Filters for the list tabs' cells.
"""  # noqa: 501

from django import template

register = template.Library()


@register.filter
def at_least(value, minimum) -> bool:
    """Whether ``value`` reaches ``minimum``: a row's role level against the
    level an action needs, decided where the row is known so that a shared
    cell is handed only the answer (``cells/menu_action.html``)."""
    return value >= minimum
