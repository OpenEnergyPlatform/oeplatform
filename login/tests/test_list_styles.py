"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The dashboard list's stylesheets, read as stylesheets (#2617, spec #2613).

``dash_list.css`` holds what every list has; ``tables_tab.css`` and
``datasets_tab.css`` each one tab's columns and cells, and the container
queries that collapse its columns. Those queries hide columns by class name
at widths measured for that tab, and both tabs have a ``c-topics`` and a
``c-created``: each tab's columns would collapse at the other's widths unless
every rule in the queries is scoped to its own tab (#2617, #2622). happy-dom
has no layout, so nothing else would notice: these tests read the rules
instead.
"""  # noqa: 501

import re
from pathlib import Path

from django.test import SimpleTestCase

STATIC = Path(__file__).resolve().parents[1] / "static" / "login"
TEMPLATES = Path(__file__).resolve().parents[1] / "templates" / "login"

TABLES_SCOPE = "#tables-tab"
DATASETS_SCOPE = "#datasets-tab"
# Each tab's stylesheet, and the tab its container queries are scoped to.
SCOPES = {"tables_tab.css": TABLES_SCOPE, "datasets_tab.css": DATASETS_SCOPE}
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


def hidden_by_queries(name):
    """Every selector a container query in ``name`` hides."""
    return {
        selector
        for context, selectors, declarations in rules(stylesheet(name))
        if context and "display: none" in declarations
        for selector in selectors
    }


class ScopedCollapseTests(SimpleTestCase):
    def test_every_rule_inside_a_container_query_is_scoped_to_its_own_tab(self):
        for name, scope in SCOPES.items():
            for context, selectors, _ in rules(stylesheet(name)):
                if not any(at.startswith("@container") for at in context):
                    continue
                for selector in selectors:
                    with self.subTest(stylesheet=name, selector=selector):
                        self.assertTrue(
                            selector.startswith(scope + " "),
                            f"{selector!r} in {context} is not scoped to {scope}",
                        )

    def test_the_tables_tab_still_collapses_its_columns(self):
        """The scope check above would pass on a file with no queries left."""
        hidden = hidden_by_queries("tables_tab.css")
        for column in (".c-created", ".c-topics", ".c-review", ".c-ds"):
            self.assertIn(f"{TABLES_SCOPE} {column}", hidden)

    def test_the_datasets_tab_collapses_its_columns(self):
        hidden = hidden_by_queries("datasets_tab.css")
        for column in (".c-created", ".c-topics"):
            self.assertIn(f"{DATASETS_SCOPE} {column}", hidden)

    def test_neither_tab_names_the_other(self):
        for name, scope in SCOPES.items():
            others = set(SCOPES.values()) - {scope}
            for _, selectors, _ in rules(stylesheet(name)):
                for selector in selectors:
                    for other in others:
                        with self.subTest(stylesheet=name, selector=selector):
                            self.assertNotIn(other, selector)


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


class TabPageTests(SimpleTestCase):
    def test_every_tab_loads_the_generic_styles_before_its_own(self):
        """The frame links dash_list.css, then the tab's ``list-styles``."""
        frame = (TEMPLATES / "list_tab.html").read_text()
        generic = frame.index("{% static 'login/dash_list.css' %}")
        self.assertLess(generic, frame.index("{% block list-styles %}"))
        self.assertLess(
            frame.index("{% block after-head %}"),
            generic,
        )

    def test_each_tab_adds_its_styles_without_replacing_the_frames(self):
        for template, sheet in (
            ("user_tables.html", "tables_tab.css"),
            ("user_datasets.html", "datasets_tab.css"),
        ):
            with self.subTest(template=template):
                page = (TEMPLATES / template).read_text()
                styles = re.search(
                    r"{% block list-styles %}(.*?){% endblock list-styles %}",
                    page,
                    re.S,
                )
                self.assertIn(f"{{% static 'login/{sheet}' %}}", styles.group(1))
                # overriding after-head would drop dash_list.css
                self.assertNotIn("{% block after-head %}", page)
