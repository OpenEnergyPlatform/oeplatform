"""Every list of tags is searchable, sortable and, in the sidebar, collapsed.

There are three of them and each rendered its whole vocabulary at once -- ~825
pills in the factsheet editor and on the administration page, 273 in the
factsheet overview's filter. The showing and hiding is browser-side and tested
with vitest (`dataedit/static/dataedit/__tests__/tag_list.test.js`); what is
asserted here is what the server has to put on the page for it to work: the
controls, the markup contract, and the usage number the ordering depends on.

That number is deliberately not `Tag.usage_count`, which counts only table
searches -- so a test pins that too.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

import re

from base.tests import TestViewsTestCase
from modelview.tests.corpus import seed_corpus

SHEETTYPES = ("model", "framework")


def tag_items(html):
    """The `[data-tag-name]` items, as (name, usage) pairs in render order."""
    return [
        (m.group("name"), int(m.group("usage")))
        for m in re.finditer(
            r'data-tag-name="(?P<name>[^"]*)"\s+data-tag-usage="(?P<usage>\d+)"', html
        )
    ]


class TagListControlsTestCase(TestViewsTestCase):

    def setUp(self):
        self.corpus = {
            t: seed_corpus(sheettype=t, factsheets=3, tags=210, corrupted=0)
            for t in SHEETTYPES
        }

    def list_html(self, sheettype):
        return self.get(
            "modelview:modellist", kwargs={"sheettype": sheettype}
        ).content.decode("utf-8")

    def editor_html(self, sheettype):
        return self.get(
            "modelview:edit",
            kwargs={
                "sheettype": sheettype,
                "pk": self.corpus[sheettype].factsheets[0].pk,
            },
            logged_in=True,
        ).content.decode("utf-8")


class TestTheFactsheetOverviewSidebar(TagListControlsTestCase):

    def test_it_offers_a_search_box(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                self.assertIn("data-tag-search", self.list_html(sheettype))

    def test_it_offers_a_sort_control(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                self.assertIn("data-tag-sort", self.list_html(sheettype))

    def test_it_offers_an_expand_control(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                self.assertIn("data-tag-expand", self.list_html(sheettype))

    def test_every_tag_carries_a_name_and_a_usage_count(self):
        """One item per distinct tag in use by that sheet type -- the bound
        T4 established, now also carrying what the ordering reads."""
        from dataedit.models import Tag
        from modelview.helper import getClasses

        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                cls, _ = getClasses(sheettype)
                in_use = (
                    Tag.objects.filter(factsheets__in=cls.objects.all())
                    .distinct()
                    .count()
                )

                items = tag_items(self.list_html(sheettype))

                self.assertTrue(in_use)
                self.assertEqual(len(items), in_use)

    def test_the_whole_list_is_still_rendered(self):
        """Collapsing is browser-side, so a reader without javascript sees
        what they saw before rather than ten tags and no way to the rest."""
        sheettype = "model"
        html = self.list_html(sheettype)

        offered = {name for name, _ in tag_items(html)}
        in_use = set(
            self.corpus[sheettype].factsheets[0].tags.values_list("name", flat=True)
        )
        self.assertTrue(in_use)
        self.assertTrue(in_use.issubset(offered))

    def test_the_usage_count_is_real_attachments_not_usage_count_field(self):
        """`Tag.usage_count` is incremented only by table search in dataedit.

        It is 0 for every tag a factsheet uses, so a page ordering by it would
        put the vocabulary in an arbitrary order and look deliberate.
        """
        sheettype = "model"
        shared = self.corpus[sheettype].tags[0]
        for other in self.corpus[sheettype].factsheets:
            other.tags.add(shared)

        items = dict(tag_items(self.list_html(sheettype)))

        self.assertEqual(items[shared.name], len(self.corpus[sheettype].factsheets))
        self.assertEqual(shared.usage_count, 0)
        self.assertGreater(items[shared.name], shared.usage_count)

    def test_the_filter_list_still_costs_no_extra_query(self):
        """The usage annotation rides on the query that was already made."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from modelview.tests.test_list_payload import view_queries

        with CaptureQueriesContext(connection) as captured:
            self.list_html("model")

        self.assertEqual(len(view_queries(captured)), 3)


class TestTheSidebarOrder(TagListControlsTestCase):
    """Whatever grows goes last.

    "Fields" is the column chooser -- the only way to reach the columns the
    page-sized payload leaves out -- and the tag list above it grows with the
    number of tags in use (273 on production). Expanding the tags used to push
    the chooser off the screen.
    """

    def test_fields_comes_before_tags(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                html = self.list_html(sheettype)
                sidebar = (
                    html[: html.index("factsheets_content")]
                    if ("factsheets_content" in html)
                    else html
                )

                self.assertLess(
                    sidebar.index("<h3>Fields</h3>"),
                    sidebar.index("<h3>Tags</h3>"),
                )

    def test_both_sections_are_still_there(self):
        html = self.list_html("model")

        self.assertIn("<h3>Fields</h3>", html)
        self.assertIn("<h3>Tags</h3>", html)
        self.assertIn("apply_filter", html)


class TestTheFactsheetTagSelector(TagListControlsTestCase):
    """The editor's Tags tab: search and sort, but no collapsed limit.

    This is the place you come to FIND a tag, so hiding options behind an
    expander would defeat it.
    """

    def test_it_offers_a_search_box(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                self.assertIn("data-tag-search", self.editor_html(sheettype))

    def test_it_offers_a_sort_control(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                self.assertIn("data-tag-sort", self.editor_html(sheettype))

    def test_it_does_not_collapse_the_options(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                self.assertNotIn("data-tag-expand", self.editor_html(sheettype))

    def test_every_offered_tag_carries_its_usage(self):
        items = tag_items(self.editor_html("model"))

        self.assertEqual(len(items), len(self.corpus["model"].tags))
        self.assertTrue(all(usage >= 0 for _, usage in items))
