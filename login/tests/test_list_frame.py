"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The list tabs' shared frame (spec #2613, prefactor): the view bases and base
templates name nothing a tab lists, and the shared status cell says what each
state says. The tables tab's own suites prove the frame changed nothing for
it; these hold what a second tab will rely on.
"""  # noqa: 501

import ast
import re
from datetime import datetime
from datetime import timezone as dt_timezone
from pathlib import Path

from django.template.loader import render_to_string
from django.test import SimpleTestCase
from django.utils.html import strip_tags

LOGIN = Path(__file__).resolve().parent.parent
BASES = (
    LOGIN / "templates/login/list_tab.html",
    LOGIN / "templates/login/partials/list_region.html",
    LOGIN / "templates/login/partials/cells/menu_action.html",
    LOGIN / "templates/login/partials/cells/status.html",
    LOGIN / "templates/login/partials/cells/chips.html",
)
STATUS = "login/partials/cells/status.html"


def _text(html) -> str:
    return " ".join(strip_tags(html).split())


class TheBasesNameNoTableTests(SimpleTestCase):
    def test_the_view_bases_import_no_model(self):
        tree = ast.parse((LOGIN / "list_views.py").read_text())
        modules = [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        ] + [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        ]
        for module in modules:
            with self.subTest(module=module):
                self.assertFalse(module.endswith("models"), module)
                self.assertFalse(module.startswith(("dataedit", "api")), module)
                self.assertNotIn("table", module)

    def test_the_base_templates_carry_no_table_id_event_or_copy(self):
        for path in BASES:
            source = re.sub(
                r"{% comment %}.*?{% endcomment %}", "", path.read_text(), flags=re.S
            )
            # the HTML element and its Bootstrap classes are not a Table
            source = re.sub(
                r"</?table\b|\b(dash-)?table(-wrap)?\b(?=[ \"])", "", source
            )
            with self.subTest(template=path.name):
                self.assertNotRegex(source.lower(), r"table")


class StatusCellTests(SimpleTestCase):
    def render(self, **context):
        return _text(render_to_string(STATUS, context))

    def test_the_three_table_states_read_as_before(self):
        until = datetime(2027, 3, 4, tzinfo=dt_timezone.utc)
        self.assertEqual(self.render(status="draft"), "Draft")
        self.assertEqual(self.render(status="published"), "Published")
        self.assertEqual(
            self.render(status="embargoed", until=until), "Embargoed until 4 Mar 2027"
        )

    def test_published_reads_since_when_given_a_date(self):
        since = datetime(2026, 10, 2, 9, 30, tzinfo=dt_timezone.utc)
        self.assertEqual(
            self.render(status="published", since=since), "Published since 2 Oct 2026"
        )

    def test_a_draft_says_nothing_of_a_date(self):
        since = datetime(2026, 10, 2, tzinfo=dt_timezone.utc)
        self.assertEqual(self.render(status="draft", since=since), "Draft")
