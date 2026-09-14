"""The edit and create pages carry the page header the rest of the site has.

The overviews fill `site-header` -- the grey band under the navigation that is
being rolled out across the platform -- and the edit and create pages did not.
They opened straight into a 171-field form with an `<h1>` inside the content
and no way back to the list they were reached from.

The band's `__wizard` slot is styled for links, so it is where the breadcrumb
belongs.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

from django.urls import reverse

from base.tests import TestViewsTestCase
from modelview.tests.corpus import seed_corpus

SHEETTYPES = ("model", "framework")


class EditHeaderTestCase(TestViewsTestCase):

    def setUp(self):
        self.corpus = {
            t: seed_corpus(sheettype=t, factsheets=1, corrupted=0) for t in SHEETTYPES
        }

    def sheet(self, sheettype):
        return self.corpus[sheettype].factsheets[0]

    def edit_html(self, sheettype):
        return self.get(
            "modelview:edit",
            kwargs={"sheettype": sheettype, "pk": self.sheet(sheettype).pk},
            logged_in=True,
        ).content.decode("utf-8")

    def add_html(self, sheettype):
        return self.get(
            "modelview:modeladd", kwargs={"sheettype": sheettype}, logged_in=True
        ).content.decode("utf-8")


class TestTheGreyBand(EditHeaderTestCase):

    def test_the_edit_page_carries_it(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                self.assertIn('class="main-header"', self.edit_html(sheettype))

    def test_the_create_page_carries_it(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                self.assertIn('class="main-header"', self.add_html(sheettype))

    def test_the_heading_is_not_repeated_inside_the_form(self):
        """The band carries the heading now; the old one sat in the content."""
        for sheettype, label in (("model", "Model"), ("framework", "Framework")):
            with self.subTest(sheettype=sheettype):
                self.assertNotIn("<h1>%s</h1>" % label, self.edit_html(sheettype))


class TestTheBreadcrumb(EditHeaderTestCase):
    """A form 171 fields long needs a way back that is not the browser button."""

    def overview_url(self, sheettype):
        return reverse("modelview:modellist", kwargs={"sheettype": sheettype})

    def test_the_edit_page_links_back_to_the_overview(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                self.assertIn(self.overview_url(sheettype), self.edit_html(sheettype))

    def test_the_create_page_links_back_to_the_overview(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                self.assertIn(self.overview_url(sheettype), self.add_html(sheettype))

    def test_the_edit_page_links_back_to_the_factsheet_itself(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                sheet = self.sheet(sheettype)
                detail = reverse(
                    "modelview:show-factsheet",
                    kwargs={"sheettype": sheettype, "pk": sheet.pk},
                )

                html = self.edit_html(sheettype)

                self.assertIn(detail, html)
                self.assertIn(sheet.model_name, html)

    def test_the_create_page_says_it_is_new_rather_than_naming_a_factsheet(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                html = self.add_html(sheettype)

                self.assertIn("New %s factsheet" % sheettype, html)
                self.assertNotIn("show-factsheet", html)
