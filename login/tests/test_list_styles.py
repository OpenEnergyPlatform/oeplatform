"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The dashboard list's stylesheets, read as stylesheets (#2617, spec #2613).

``dash_list.css`` holds what every list has; ``tables_tab.css`` the tables
tab's columns, cells and drawer, and the container queries that collapse its
columns. Those queries hide columns by class name at widths measured for the
tables tab, so a second list with a column of the same name (``c-topics``,
``c-created``) would collapse at the tables' widths unless every rule in them
is scoped to the tables tab. happy-dom has no layout, so nothing else would
notice: these tests read the rules instead.
"""  # noqa: 501

import re
from pathlib import Path

from django.test import SimpleTestCase

STATIC = Path(__file__).resolve().parents[1] / "static" / "login"
TEMPLATES = Path(__file__).resolve().parents[1] / "templates" / "login"

TABLES_SCOPE = "#tables-tab"
# a column's class: what a tab's container queries hide and place
COLUMN_CLASS = re.compile(r"\.c-[\w-]+")


def rules(css):
    """Every style rule as ``(at_rules, selectors, declarations)``.

    ``at_rules`` are the preludes of the at-rules it sits in, outermost
    first; comments are dropped. Enough of CSS for these stylesheets: no
    strings or escapes holding braces.
    """
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    found = []

    def block(pos, context):
        prelude_start = pos
        while pos < len(css):
            char = css[pos]
            if char == "{":
                prelude = " ".join(css[prelude_start:pos].split())
                if prelude.startswith("@"):
                    pos = block(pos + 1, context + (prelude,))
                else:
                    end = css.index("}", pos)
                    selectors = tuple(" ".join(s.split()) for s in prelude.split(","))
                    found.append(
                        (context, selectors, " ".join(css[pos + 1 : end].split()))
                    )
                    pos = end
                prelude_start = pos + 1
            elif char == "}":
                return pos
            pos += 1
        return pos

    block(0, ())
    return found


def stylesheet(name):
    return (STATIC / name).read_text()


class ScopedCollapseTests(SimpleTestCase):
    def test_every_rule_inside_a_container_query_is_scoped_to_the_tables_tab(self):
        for name in ("dash_list.css", "tables_tab.css"):
            for context, selectors, _ in rules(stylesheet(name)):
                if not any(at.startswith("@container") for at in context):
                    continue
                for selector in selectors:
                    with self.subTest(stylesheet=name, selector=selector):
                        self.assertTrue(
                            selector.startswith(TABLES_SCOPE + " "),
                            f"{selector!r} in {context} is not scoped to "
                            f"{TABLES_SCOPE}",
                        )

    def test_the_tables_tab_still_collapses_its_columns(self):
        """The scope check above would pass on a file with no queries left."""
        hidden = {
            selector
            for context, selectors, declarations in rules(stylesheet("tables_tab.css"))
            if context and "display: none" in declarations
            for selector in selectors
        }
        for column in (".c-created", ".c-topics", ".c-review", ".c-ds"):
            self.assertIn(f"{TABLES_SCOPE} {column}", hidden)


class GenericStylesheetTests(SimpleTestCase):
    def setUp(self):
        self.generic = rules(stylesheet("dash_list.css"))

    def test_it_names_no_column_class(self):
        for _, selectors, _ in self.generic:
            for selector in selectors:
                with self.subTest(selector=selector):
                    self.assertIsNone(COLUMN_CLASS.search(selector))

    def test_it_names_no_tab(self):
        for _, selectors, _ in self.generic:
            for selector in selectors:
                with self.subTest(selector=selector):
                    self.assertNotIn("#", selector)

    def test_it_holds_no_container_query(self):
        """Collapse widths are measured per tab, so they live with the tab."""
        for context, _, _ in self.generic:
            self.assertFalse(any(at.startswith("@container") for at in context))

    def test_it_holds_the_list_container(self):
        self.assertIn(
            (
                (),
                (".dash",),
                "--dash-muted: #6c757d; --dash-primary: #2972a6; "
                "--dash-secondary: #1f567d; container-type: inline-size;",
            ),
            self.generic,
        )


class TablesPageTests(SimpleTestCase):
    def test_every_tab_loads_the_generic_styles_before_its_own(self):
        """The frame links dash_list.css, then the tab's ``list-styles``."""
        frame = (TEMPLATES / "list_tab.html").read_text()
        generic = frame.index("{% static 'login/dash_list.css' %}")
        self.assertLess(generic, frame.index("{% block list-styles %}"))
        self.assertLess(
            frame.index("{% block after-head %}"),
            generic,
        )

    def test_the_tables_tab_adds_its_styles_without_replacing_the_frames(self):
        page = (TEMPLATES / "user_tables.html").read_text()
        styles = re.search(
            r"{% block list-styles %}(.*?){% endblock list-styles %}", page, re.S
        )
        self.assertIn("{% static 'login/tables_tab.css' %}", styles.group(1))
        # overriding after-head would drop dash_list.css
        self.assertNotIn("{% block after-head %}", page)
