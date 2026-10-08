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


class _Elements(HTMLParser):
    """Collects the markup of every element `matches` picks out of its
    attributes, children included, by counting how deep the parser is inside
    it. A matching element inside another is part of the outer one's markup,
    not an element of its own."""

    VOID = {"area", "br", "col", "hr", "img", "input", "link", "meta", "source"}

    def __init__(self, matches):
        super().__init__(convert_charrefs=False)
        self.matches = matches
        self.depth = 0
        self.found = []

    def handle_starttag(self, tag, attrs):
        if self.depth == 0:
            if not self.matches(dict(attrs)):
                return
            self.found.append([])
        self.found[-1].append(self.get_starttag_text())
        if tag not in self.VOID:
            self.depth += 1

    def handle_endtag(self, tag):
        if self.depth and tag not in self.VOID:
            self.found[-1].append(f"</{tag}>")
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.found[-1].append(data)

    def handle_entityref(self, name):
        self.handle_data(f"&{name};")

    def handle_charref(self, name):
        self.handle_data(f"&#{name};")


def _markup(html, matches):
    parser = _Elements(matches)
    parser.feed(html)
    return ["".join(parts) for parts in parser.found]


def element_markup(html: str, element_id: str) -> str:
    """The element carrying `element_id` with everything inside it, or ""
    when there is none: for asserting on what an element contains, where
    `element_with_id` gives only its opening tag."""
    found = _markup(html, lambda attrs: attrs.get("id") == element_id)
    return found[0] if found else ""


def elements_with_class(html: str, css_class: str) -> list[str]:
    """The markup of every element carrying `css_class`, in page order: for
    asserting how many of them a page has and what each one contains."""
    return _markup(html, lambda attrs: css_class in (attrs.get("class") or "").split())


def text(markup: str) -> str:
    """What `markup` reads as: its text without tags, whitespace collapsed,
    so an assertion on a sentence does not depend on how djlint wrapped it."""
    return " ".join(re.sub(r"<[^>]*>", "", markup).split())


def table_rows(html: str) -> list[tuple[int, str]]:
    """`(depth, row)` for every `<tr>` on the page: how many rows of its own
    table were still open when it started, and its opening tag.

    Counted per table, because a cell may hold a table of its own (the
    checklists do), and a row in that table is not nested in the outer row.
    """
    open_rows, rows = [0], []
    for match in re.finditer(r"<(/?)(tr|table)\b[^>]*>", html, re.IGNORECASE):
        closing, tag = match.group(1), match.group(2).lower()
        if tag == "table":
            if closing:
                open_rows.pop()
            else:
                open_rows.append(0)
        elif closing:
            open_rows[-1] -= 1
        else:
            rows.append((open_rows[-1], match.group(0)))
            open_rows[-1] += 1
    return rows


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
