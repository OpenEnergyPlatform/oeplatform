"""The model and framework detail pages, as a browser receives them.

Both are one record page (#2655, spec #2632 "Record pages"): the page header,
then the record toolbar (the factsheet's tags at the start, Delete then Edit
at the end), then the sections stacked as section cards, every one open. A
section's header is a real button with `aria-expanded`, replacing Bootstrap
3's `collapse in` links, which Bootstrap 5 reads as closed. The "?" beside a
field is a field help button: focusable, named, its tooltip set up by the
shell.

Earlier (#2634): both pages dropped the factsheet base template's tooltip
set-up, so none of the help icons opened; the framework page also carried a
`title=` pasted into a class attribute and a table row nested in a row.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re

from base.tests import TestViewsTestCase
from base.tests.html_tree import parse
from modelview.tests.corpus import seed_corpus
from modelview.tests.html import table_rows

SHEETTYPES = ("model", "framework")

#: The shell's set-up of every field help's tooltip (base/_feedback.html).
TOOLTIP_SETUP = 'root.querySelectorAll(".field-help")'


class DetailPageTestCase(TestViewsTestCase):
    def setUp(self):
        self.pk = {
            t: seed_corpus(sheettype=t, factsheets=1, corrupted=0).factsheets[0].pk
            for t in SHEETTYPES
        }

    def detail_html(self, sheettype, logged_in=False):
        return self.get(
            "modelview:show-factsheet",
            kwargs={"sheettype": sheettype, "pk": self.pk[sheettype]},
            logged_in=logged_in,
        ).content.decode()

    def main(self, sheettype, logged_in=False):
        return parse(self.detail_html(sheettype, logged_in)).find(
            css_class="content__main"
        )


class RecordLayoutTest(DetailPageTestCase):
    def record_parts(self, main):
        return [
            node
            for node in main.iter()
            if node.has_class("record-toolbar") or node.has_class("section-card")
        ]

    def test_both_pages_are_a_toolbar_then_section_cards(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                parts = self.record_parts(self.main(sheettype, logged_in=True))

                self.assertTrue(parts[0].has_class("record-toolbar"))
                self.assertGreater(len(parts), 1)
                self.assertTrue(all(p.has_class("section-card") for p in parts[1:]))
                # Stacked: one parent holds the toolbar and every section.
                self.assertEqual({id(p.parent) for p in parts}, {id(parts[0].parent)})

    def test_every_section_header_is_a_button_and_every_section_open(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                main = self.main(sheettype)
                for section in main.find_all(css_class="section-card"):
                    toggle = section.find("button")
                    self.assertEqual(toggle.parent.tag, "h2")
                    self.assertEqual(toggle.attrs["type"], "button")
                    self.assertEqual(toggle.attrs["aria-expanded"], "true")
                    body = [
                        n
                        for n in section.iter()
                        if n.attrs.get("id") == toggle.attrs["aria-controls"]
                    ]
                    self.assertEqual(len(body), 1)
                    self.assertIn("show", body[0].classes)
                    self.assertIsNotNone(body[0].find(css_class="card-body"))

    def test_no_bootstrap_3_collapse_is_left(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                classes = re.findall(r'class="([^"]*)"', self.detail_html(sheettype))
                self.assertEqual([c for c in classes if "in" in c.split()], [])

    def test_the_toolbar_holds_the_tags_then_delete_then_edit(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                toolbar = self.main(sheettype, logged_in=True).find(
                    css_class="record-toolbar"
                )
                actions = toolbar.find(css_class="record-toolbar__actions")
                delete, edit = actions.elements

                self.assertIn("hx-delete", delete.attrs)
                self.assertIn("btn-outline-danger", delete.classes)
                self.assertIn("hx-confirm", delete.attrs)
                self.assertIn("data-confirm-danger", delete.attrs)
                self.assertEqual(edit.tag, "a")
                self.assertIn("btn-primary", edit.classes)
                self.assertEqual(edit.text(), "Edit")

    def test_signed_out_there_is_no_action(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                html = self.detail_html(sheettype)
                self.assertNotIn("record-toolbar__actions", html)
                self.assertNotIn('hx-delete="', html)


class FieldHelpTest(DetailPageTestCase):
    def test_every_help_is_a_named_button_with_a_tooltip(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                helps = self.main(sheettype).find_all(css_class="field-help")

                self.assertTrue(helps)
                for help in helps:
                    self.assertEqual(help.tag, "button")
                    self.assertEqual(help.attrs["type"], "button")
                    self.assertEqual(help.attrs["data-bs-toggle"], "tooltip")
                    self.assertRegex(help.attrs["aria-label"], r"^Help on \S")
                    self.assertTrue(help.attrs["title"].strip())

    def test_the_tooltips_are_set_up_and_no_old_icon_is_left(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                html = self.detail_html(sheettype)
                self.assertIn(TOOLTIP_SETUP, html)
                self.assertNotIn("fa-question", html)

    def test_the_pages_own_scripts_stay(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                self.assertIn("htmx:responseError", self.detail_html(sheettype))


class DetailMarkupTest(DetailPageTestCase):
    def test_no_class_attribute_carries_a_title(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                classes = re.findall(r'class="([^"]*)"', self.detail_html(sheettype))
                self.assertEqual([c for c in classes if "title=" in c], [])

    def test_no_table_row_is_nested_in_another(self):
        for sheettype in SHEETTYPES:
            for logged_in in (False, True):
                with self.subTest(sheettype=sheettype, logged_in=logged_in):
                    rows = table_rows(self.detail_html(sheettype, logged_in))
                    self.assertTrue(rows)
                    self.assertEqual([r for d, r in rows if d], [])
