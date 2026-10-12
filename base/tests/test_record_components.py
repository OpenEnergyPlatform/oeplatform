"""The section card and field help (#2655), rendered on their own, and a scan
that keeps the variants they replaced from coming back.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string
from django.test import SimpleTestCase

from base.tests.html_tree import parse


class SectionCardTest(SimpleTestCase):
    def test_the_header_is_an_open_button_controlling_the_body(self):
        root = parse(
            render_to_string(
                "components/section_card.html",
                {
                    "id": "s",
                    "title": "Openness",
                    "body": "styleguide/entries/_section_card_body.html",
                },
            )
        )
        section = root.find("section")
        toggle = section.find("button")

        self.assertEqual(section.attrs["id"], "s")
        self.assertEqual(toggle.parent.tag, "h2")
        self.assertEqual(toggle.text(), "Openness")
        self.assertEqual(toggle.attrs["aria-expanded"], "true")
        self.assertEqual(toggle.attrs["aria-controls"], "s-body")
        self.assertEqual(toggle.attrs["data-bs-target"], "#s-body")
        body = [n for n in section.iter() if n.attrs.get("id") == "s-body"][0]
        self.assertEqual(body.classes, ["collapse", "show"])
        self.assertIn("section's content", body.text())


class FieldHelpTest(SimpleTestCase):
    def test_a_named_button_with_its_help_as_tooltip(self):
        root = parse(
            render_to_string(
                "components/field_help.html",
                {"label": "Acronym", "text": 'Short "name"'},
            )
        )
        button = root.find("button")

        self.assertEqual(button.attrs["type"], "button")
        self.assertEqual(button.attrs["aria-label"], "Help on Acronym")
        self.assertEqual(button.attrs["title"], 'Short "name"')
        self.assertEqual(button.attrs["data-bs-toggle"], "tooltip")
        self.assertEqual(button.text(), "")


class NoOldVariantTest(SimpleTestCase):
    """No template draws the old "?" icon or a Bootstrap 3 open collapse."""

    OLD = re.compile(r"fa-question\"|\bcollapse in\b|\bexpand in\b")

    def test_no_template_keeps_an_old_variant(self):
        offenders = [
            str(path.relative_to(settings.BASE_DIR))
            for path in Path(settings.BASE_DIR).glob("*/templates/**/*.html")
            if self.OLD.search(path.read_text(encoding="utf-8"))
        ]
        self.assertEqual(offenders, [])
