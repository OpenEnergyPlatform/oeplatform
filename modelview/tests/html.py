"""Reading checkbox state out of a rendered page.

Three modules in this app assert on rendered checkboxes -- the list page's tag
filter, the edit form's tag selector, and the filter list's contents -- and had
grown three near-identical scrapers between them. One is enough, and it keeps
the "which attribute is on which line" knowledge in a single place: djlint
reformats these templates on every commit, so any scraper that assumed an
attribute order would break on a purely cosmetic change.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re

#: One `<input ...>` element, whole, so nothing here depends on the order
#: djlint happens to leave the attributes in.
_INPUT = re.compile(r"<input\b[^>]*>", re.IGNORECASE)
_VALUE = re.compile(r'value="([^"]*)"')


def checkboxes(html: str, css_class: str) -> list[tuple[str, bool]]:
    """Every `<input>` carrying `css_class`, as (value, checked) pairs.

    Scoping by class is not cosmetic: the list page's sidebar also renders
    `checked` field-visibility checkboxes, so an unscoped search would assert
    something else entirely.
    """
    found = []
    for element in _INPUT.findall(html):
        if css_class not in element:
            continue
        value = _VALUE.search(element)
        found.append((value.group(1) if value else "", "checked" in element))
    return found


def offered_values(html: str, css_class: str) -> list[str]:
    """The values of those checkboxes, in render order."""
    return [value for value, _checked in checkboxes(html, css_class)]


def checked_values(html: str, css_class: str) -> set[str]:
    """The values of the ones rendered pre-checked."""
    return {value for value, checked in checkboxes(html, css_class) if checked}
