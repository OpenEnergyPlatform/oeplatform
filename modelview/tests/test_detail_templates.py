"""The model and framework detail pages, as a browser receives them.

Both pages override the factsheet base template's script block. They did so
without `{{ block.super }}`, which dropped the one line that initialises
Bootstrap's tooltips, so none of the help icons on either page opened (0 of 47
on a model, 0 of 41 on a framework). The framework page also carried a
`title=` pasted into a class attribute and a table row nested in a row.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re

from base.tests import TestViewsTestCase
from modelview.tests.corpus import seed_corpus
from modelview.tests.html import table_rows

SHEETTYPES = ("model", "framework")

#: The factsheet base template's tooltip set-up.
TOOLTIP_SETUP = """$('[data-bs-toggle="tooltip"]').tooltip();"""


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


class TooltipSetupTest(DetailPageTestCase):
    def test_the_detail_pages_initialise_their_tooltips(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                html = self.detail_html(sheettype)
                self.assertIn('data-bs-toggle="tooltip"', html)
                self.assertIn(TOOLTIP_SETUP, html)

    def test_the_pages_own_scripts_stay(self):
        """`block.super` is added to the block, not swapped in for it."""
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                self.assertIn("htmx:responseError", self.detail_html(sheettype))


def section_bodies(html):
    """The class attribute of every collapsible section body on the page,
    read off each `<div>` whole so the order of its attributes does not
    matter."""
    found = []
    for div in re.findall(r"<div\b[^>]*>", html):
        classes = re.search(r'\bclass="([^"]*)"', div)
        if classes and re.search(r"\b(collapse|expand)\b", classes.group(1)):
            found.append(classes.group(1))
    return found


class DetailMarkupTest(DetailPageTestCase):
    def test_no_class_attribute_carries_a_title(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                classes = re.findall(r'class="([^"]*)"', self.detail_html(sheettype))
                self.assertEqual([c for c in classes if "title=" in c], [])

    def test_every_section_body_is_a_card_body(self):
        """The stray `title=` stood where the model page has `card-body`, so
        four framework sections went without the card's padding."""
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                classes = section_bodies(self.detail_html(sheettype))
                self.assertTrue(classes)
                self.assertEqual([c for c in classes if "card-body" not in c], [])

    def test_no_table_row_is_nested_in_another(self):
        for sheettype in SHEETTYPES:
            for logged_in in (False, True):
                with self.subTest(sheettype=sheettype, logged_in=logged_in):
                    rows = table_rows(self.detail_html(sheettype, logged_in))
                    self.assertTrue(rows)
                    self.assertEqual([r for d, r in rows if d], [])
