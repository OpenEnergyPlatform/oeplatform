"""A rendered page as a tree, for asserting on its structure.

The string scrapers in ``modelview/tests/html.py`` answer "what does this
element contain"; a page header needs "where does this element sit" (is the
``h1`` inside the trail's last item, inside the band), which needs parents.
Standard library only: the parser forgives what browsers forgive (an end tag
closes whatever is still open inside it; an unclosed ``<p>`` ends at its
parent's end), which is all the platform's templates ask of it.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from html.parser import HTMLParser

VOID = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "source",
    "track",
    "wbr",
}
# Their content is not text a reader meets.
NOT_TEXT = {"script", "style", "template", "noscript"}


class Node:
    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children = []

    @property
    def classes(self):
        return (self.attrs.get("class") or "").split()

    def has_class(self, css_class):
        return css_class in self.classes

    @property
    def elements(self):
        return [child for child in self.children if isinstance(child, Node)]

    def iter(self):
        """Every element below this one, in document order."""
        for child in self.elements:
            yield child
            yield from child.iter()

    def find_all(self, tag=None, css_class=None):
        return [
            node
            for node in self.iter()
            if (tag is None or node.tag == tag)
            and (css_class is None or node.has_class(css_class))
        ]

    def find(self, tag=None, css_class=None):
        found = self.find_all(tag, css_class)
        return found[0] if found else None

    @property
    def ancestors(self):
        node = self.parent
        while node is not None:
            yield node
            node = node.parent

    def within(self, other):
        return any(ancestor is other for ancestor in self.ancestors)

    def text(self, skip=lambda node: False):
        """What the element reads as, whitespace collapsed; elements for which
        `skip` is true are left out with everything inside them."""
        return " ".join(" ".join(self._texts(skip)).split())

    def _texts(self, skip):
        for child in self.children:
            if isinstance(child, str):
                yield child
            elif child.tag not in NOT_TEXT and not skip(child):
                yield from child._texts(skip)


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", {}, None)
        self.open = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), self.open)
        self.open.children.append(node)
        if tag not in VOID:
            self.open = node

    def handle_startendtag(self, tag, attrs):
        self.open.children.append(Node(tag, dict(attrs), self.open))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        node = self.open
        while node is not self.root and node.tag != tag:
            node = node.parent
        if node is not self.root:
            self.open = node.parent

    def handle_data(self, data):
        self.open.children.append(data)


def parse(html):
    builder = _TreeBuilder()
    builder.feed(html)
    builder.close()
    return builder.root
