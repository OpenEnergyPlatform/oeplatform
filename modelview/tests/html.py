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
from html.parser import HTMLParser

#: One `<input ...>` element, whole, so nothing here depends on the order
#: djlint happens to leave the attributes in.
_INPUT = re.compile(r"<input\b[^>]*>", re.IGNORECASE)
_VALUE = re.compile(r'value="([^"]*)"')


def element_with_id(html: str, element_id: str) -> str:
    """The opening tag of the element carrying `element_id`, whole.

    Whole, so that nothing here depends on the order djlint happens to leave
    the attributes in -- or on whether it put them on one line. An assertion
    written as the literal `id="x" hidden` breaks on a purely cosmetic
    reformat, which is exactly what happened when djlint was updated.
    """
    found = re.search(r"<[a-zA-Z][^>]*\bid=\"%s\"[^>]*>" % re.escape(element_id), html)
    return found.group(0) if found else ""


class _Element(HTMLParser):
    """Collects the markup of the first element carrying one id, children
    included, by counting how deep the parser is inside it."""

    VOID = {"area", "br", "col", "hr", "img", "input", "link", "meta", "source"}

    def __init__(self, element_id):
        super().__init__(convert_charrefs=False)
        self.element_id = element_id
        self.depth = 0
        self.done = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if self.done:
            return
        if self.depth == 0 and dict(attrs).get("id") != self.element_id:
            return
        self.parts.append(self.get_starttag_text())
        if tag not in self.VOID:
            self.depth += 1
        elif self.depth == 0:
            self.done = True

    def handle_endtag(self, tag):
        if self.depth and not self.done and tag not in self.VOID:
            self.parts.append(f"</{tag}>")
            self.depth -= 1
            self.done = self.depth == 0

    def handle_data(self, data):
        if self.depth and not self.done:
            self.parts.append(data)

    def handle_entityref(self, name):
        self.handle_data(f"&{name};")

    def handle_charref(self, name):
        self.handle_data(f"&#{name};")


def element_markup(html: str, element_id: str) -> str:
    """The element carrying `element_id` with everything inside it, or ""
    when there is none: for asserting on what an element contains, where
    `element_with_id` gives only its opening tag."""
    parser = _Element(element_id)
    parser.feed(html)
    return "".join(parser.parts)


def text(markup: str) -> str:
    """What `markup` reads as: its text without tags, whitespace collapsed,
    so an assertion on a sentence does not depend on how djlint wrapped it."""
    return " ".join(re.sub(r"<[^>]*>", "", markup).split())


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
