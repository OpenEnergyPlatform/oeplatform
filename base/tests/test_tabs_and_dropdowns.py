"""Underline tabs and the house dropdown (#2648), as a browser receives them.

Tabs used to be drawn four ways: Bootstrap's boxed `nav-tabs` (the factsheet
editor, the table page's view switcher, the metadata viewer), `.table-tabs`
(the table page), `.fullwidth-tabs` (the two peer review pages) and
`.pages-nav-tabs` (the dashboard). Now every tab row is the `tabs` component:
`nav tabs` on the row, `nav-link` on each tab, at most one aside link at its
end, and nothing else in it. What the row looks like (the underline, the
primary bar, the aside staying in view while the row scrolls) is the theme's,
checked in the browser rather than here.

Every dropdown takes the navbar dropdown's look from the theme's
`.dropdown-menu`; there is no markup to assert beyond the catalogue entry.

The dashboard's tables tab keeps its own list controls (#2659).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from base.tests import TestViewsTestCase
from dataedit.models import PeerReview, PeerReviewManager, Table
from modelview.tests.corpus import seed_corpus
from modelview.tests.html import elements_with_class

#: The classes the `tabs` component replaces.
RETIRED = ("nav-tabs", "table-tabs", "fullwidth-tabs", "pages-nav-tabs")

_RETIRED = re.compile(r"(?<![\w-])(%s)(?![\w-])" % "|".join(RETIRED))
_OPENING = re.compile(r"<(a|button|input)\b[^>]*>", re.IGNORECASE)
_CLASS = re.compile(r'class="([^"]*)"')


def classes(opening_tag):
    found = _CLASS.search(opening_tag)
    return found.group(1).split() if found else []


def tab_rows(html):
    """The markup of every tab row on the page, in page order."""
    return elements_with_class(html, "tabs")


def controls(row):
    """Every link, button and input in a tab row, as its opening tag."""
    return [m.group(0) for m in _OPENING.finditer(row)]


def tabs(row):
    return [c for c in controls(row) if "nav-link" in classes(c)]


def asides(row):
    return [c for c in controls(row) if "tabs__aside" in classes(c)]


def others(row):
    """Controls in the row that are neither a tab, the aside link, nor an
    item of a tab's own dropdown."""
    own = {"nav-link", "tabs__aside", "dropdown-item"}
    return [c for c in controls(row) if not own & set(classes(c))]


def active(row):
    return [c for c in tabs(row) if "active" in classes(c)]


class NoRetiredTabClassTest(SimpleTestCase):
    """No template, script or theme partial uses a class the component
    replaced. The React apps are out of scope (#2632) and keep their own."""

    def sources(self):
        base = Path(settings.BASE_DIR)
        patterns = ("*/templates/**/*.html", "*/static/**/*.js", "theming/**/*.scss")
        for pattern in patterns:
            for path in base.glob(pattern):
                parts = set(path.relative_to(base).parts)
                if parts & {"node_modules", "frontend", "site-packages", ".venv"}:
                    continue
                if path.name.endswith(".min.js") or path.parts[-2] == "vendor":
                    continue
                if path.relative_to(base).parts[0] == "static":
                    continue  # collectstatic's copy of the sources
                yield path

    def test_no_source_uses_a_retired_tab_class(self):
        found = [
            f"{path}: {match.group(1)}"
            for path in self.sources()
            for match in _RETIRED.finditer(path.read_text(encoding="utf-8"))
        ]
        self.assertEqual(found, [])

    def test_the_metadata_viewer_builds_house_tabs(self):
        script = Path(settings.BASE_DIR, "dataedit/static/metadata-viewer").joinpath(
            "metadata-viewer.js"
        )
        self.assertIn('class="nav tabs', script.read_text(encoding="utf-8"))


class TabRowAssertions:
    """What every tab row promises, whatever page it is on."""

    def assert_house_tab_row(self, row):
        opening = row[: row.index(">") + 1]
        self.assertIn("nav", classes(opening))
        self.assertTrue(tabs(row), "a tab row without a tab")
        self.assertLessEqual(len(active(row)), 1)
        self.assertEqual(others(row), [], "an action sits in the tab row")
        self.assertLessEqual(len(asides(row)), 1)
        for aside in asides(row):
            self.assertNotIn('role="tab"', aside)
            self.assertNotIn("active", classes(aside))
            self.assertIn("aria-label=", aside)
            self.assertEqual(controls(row)[-1], aside, "the aside is not at the end")


class TablePageTabsTest(TabRowAssertions, TestViewsTestCase):
    table_name = "test_tabs_table"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.table = Table.create_with_oedb_table(
            is_sandbox=True,
            name=cls.table_name,
            user=cls.user,
            column_definitions=[],
            constraints_definitions=[],
        )
        cls.review = PeerReview.objects.create(
            table=cls.table.name, reviewer=cls.user, review={}
        )
        PeerReviewManager.objects.create(opr=cls.review)

    @classmethod
    def tearDownClass(cls):
        cls.review.delete()
        cls.table.delete()
        super().tearDownClass()

    def html(self, view_name, **kwargs):
        return self.get(
            view_name, kwargs={"table": self.table_name, **kwargs}, logged_in=True
        ).content.decode()

    def test_the_table_page_has_two_house_tab_rows(self):
        rows = tab_rows(self.html("dataedit:view"))

        self.assertEqual(len(rows), 2)  # Data/Meta/Review, and the view switcher
        for row in rows:
            self.assert_house_tab_row(row)
        self.assertIn('id="tableTabs"', rows[0])
        self.assertEqual(len(active(rows[0])), 1)

    def test_the_hide_options_button_sits_beside_the_tab_row(self):
        html = self.html("dataedit:view")

        self.assertIn('id="toggleContentSideBtn"', html)
        self.assertNotIn('id="toggleContentSideBtn"', tab_rows(html)[0])

    def test_a_dropdown_in_a_tab_row_is_not_clipped_by_its_scrolling(self):
        """A tab row scrolls sideways, which would cut off a menu opening
        below it; the view switcher's menus are positioned against the
        window instead."""
        switcher = tab_rows(self.html("dataedit:view"))[1]
        toggles = [c for c in controls(switcher) if "dropdown-toggle" in classes(c)]

        self.assertEqual(len(toggles), 2)  # Graphs, Maps
        for toggle in toggles:
            self.assertIn("data-bs-popper-config=", toggle)
            self.assertIn('"strategy": "fixed"', toggle)

    def test_the_peer_review_pages_keep_their_controls_out_of_the_tab_row(self):
        for view_name, kwargs in (
            ("dataedit:peer_review_create", {}),  # the reviewer's template
            ("dataedit:peer_review_contributor", {"review_id": self.review.pk}),
        ):
            with self.subTest(view=view_name):
                html = self.html(view_name, **kwargs)
                rows = tab_rows(html)

                self.assertEqual(len(rows), 1)
                self.assert_house_tab_row(rows[0])
                self.assertIn('id="myTab"', rows[0])
                self.assertIn('id="peer_review-controls"', html)
                self.assertNotIn("peer_review-controls", rows[0])


class FactsheetEditTabsTest(TabRowAssertions, TestViewsTestCase):
    def test_the_editor_has_one_house_tab_row(self):
        for sheettype in ("model", "framework"):
            with self.subTest(sheettype=sheettype):
                sheet = seed_corpus(sheettype=sheettype, factsheets=1, corrupted=0)
                html = self.get(
                    "modelview:edit",
                    kwargs={"sheettype": sheettype, "pk": sheet.factsheets[0].pk},
                    logged_in=True,
                ).content.decode()
                rows = tab_rows(html)

                self.assertEqual(len(rows), 1)
                self.assert_house_tab_row(rows[0])


class DashboardTabsTest(TabRowAssertions, TestViewsTestCase):
    #: Each dashboard route and the tab it marks; the bare profile address
    #: opens on the datasets list.
    PAGES = (
        ("profile", "datasets"),
        ("datasets", "datasets"),
        ("tables", "tables"),
        ("reviews", "reviews"),
        ("organizations", "organizations"),
    )

    def page(self, name):
        return self.get(
            f"login:{name}", kwargs={"user_id": self.user.pk}, logged_in=True
        ).content.decode()

    def test_each_dashboard_page_marks_its_own_tab_active_in_the_markup(self):
        """The active tab used to be found by a script after the page had
        loaded; now the page arrives with it marked."""
        for name, tab in self.PAGES:
            with self.subTest(page=name):
                html = self.page(name)
                rows = [r for r in tab_rows(html) if 'aria-label="Dashboard"' in r]

                self.assertEqual(len(rows), 1)
                self.assert_house_tab_row(rows[0])
                current = active(rows[0])
                self.assertEqual(len(current), 1)
                self.assertIn('aria-current="page"', current[0])
                url = reverse(f"login:{tab}", kwargs={"user_id": self.user.pk})
                self.assertIn(f'href="{url}"', current[0])

    def test_the_row_is_a_navigation_not_a_tablist(self):
        """Its tabs are links to other pages, so the row is a `nav` and no
        tab claims `role="tab"`."""
        row = [r for r in tab_rows(self.page("tables")) if "Dashboard" in r][0]

        self.assertTrue(row.startswith("<nav"))
        self.assertNotIn('role="tab"', row)


class CatalogueEntriesTest(TabRowAssertions, TestCase):
    def entry(self, name):
        html = self.client.get(reverse("base:styleguide")).content.decode()
        found = re.search(
            r'data-entry="%s"(.*?)id="%s-source"' % (name, name), html, re.DOTALL
        )
        self.assertIsNotNone(found, f"no catalogue entry for {name}")
        return found.group(1)

    def test_tabs_are_shown_with_and_without_the_aside_link(self):
        rows = tab_rows(self.entry("tabs"))

        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assert_house_tab_row(row)
        self.assertEqual([len(asides(row)) for row in rows], [0, 1])

    def test_the_dropdown_is_shown(self):
        self.assertIn('class="dropdown-menu', self.entry("dropdown"))
