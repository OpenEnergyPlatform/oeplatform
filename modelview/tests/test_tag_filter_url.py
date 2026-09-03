"""The tag filter lives in the URL, and the filtered CSV download returns rows.

Two user-visible defects sharing one mechanism. The page kept its active
filter only in the DOM, so a filtered view could not be reloaded or shared;
and it built the "Download CSV" link with `?tags=select_<pk>` where the CSV
view filters on raw pks, so every filtered download silently returned a
header-only file -- which a user reads as "no matches" rather than as a bug.
Verified live before the fix: 0 rows where the correct value returns 59.

One query-string format, raw pks, is what removes both.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import csv
import io
import re

from base.tests import TestViewsTestCase
from dataedit.models import Tag
from modelview.tests.corpus import seed_corpus
from modelview.tests.html import checked_values

SHEETTYPES = ("model", "framework")

#: The sidebar's tag inputs. The Fields section of the same sidebar
#: legitimately renders `checked` for the default columns.
TAG_CHECKBOX = "tag-checkbox"

#: Every `select_` in the page must be part of an `id`. The prefix survives as
#: a DOM id and nowhere else -- not in a submitted value, not in a query
#: string.
_SELECT_PREFIX = re.compile(r"select_")
_SELECT_AS_ID = re.compile(r'id="select_')


def checked_sidebar_tags(html: str) -> set[str]:
    """The tag pks the sidebar renders pre-checked."""
    return checked_values(html, TAG_CHECKBOX)


class TagFilterUrlTestCase(TestViewsTestCase):
    """Two corpora, plus two tags whose factsheets are known exactly."""

    @classmethod
    def setUpTestData(cls):
        cls.corpus = {
            t: seed_corpus(sheettype=t, factsheets=6, corrupted=0, healthy_tags=0)
            for t in SHEETTYPES
        }
        # `both` is on the first two factsheets, `one` only on the first, so
        # an AND filter over the pair must return exactly one row and each
        # tag alone must return more than that.
        cls.both = {}
        cls.only_first = {}
        for sheettype in SHEETTYPES:
            sheets = cls.corpus[sheettype].factsheets
            cls.both[sheettype] = cls.corpus[sheettype].tags[0]
            cls.only_first[sheettype] = cls.corpus[sheettype].tags[1]
            sheets[0].tags.add(cls.both[sheettype], cls.only_first[sheettype])
            sheets[1].tags.add(cls.both[sheettype])

        # The corpora share one vocabulary, so a tag used by both sheet types
        # cannot show that the pre-check is scoped. This one is on a framework
        # and on nothing else.
        cls.framework_only = Tag.objects.create(
            name_normalized="framework-only", name="framework only", color=0x00FF00
        )
        cls.corpus["framework"].factsheets[0].tags.add(cls.framework_only)

    def list_page(self, sheettype, tags=None):
        query = {"tags": ",".join(tags)} if tags is not None else None
        resp = self.get(
            "modelview:modellist", kwargs={"sheettype": sheettype}, query=query
        )
        return resp.content.decode("utf-8")

    def csv_rows(self, sheettype, tags=None):
        """The data rows of a CSV download, header excluded."""
        query = {"tags": tags} if tags is not None else None
        resp = self.get(
            "modelview:download", kwargs={"sheettype": sheettype}, query=query
        )
        rows = list(csv.reader(io.StringIO(resp.content.decode("utf-8"))))
        return rows[1:]


class TestTheFilterIsRestoredFromTheUrl(TagFilterUrlTestCase):
    """`?tags=<pk>,<pk>` is the canonical home of the filter state.

    This is also where T4's removed conditional comes back -- correct this
    time, and testing a small set of selected pks rather than a queryset. With
    `.distinct()` in place a queryset test would be 273 squared rather than
    12,156 squared: harmless today, but the quadratic would still be sitting
    there waiting for the next thing that grows.
    """

    def test_one_tag_in_the_url_pre_checks_that_checkbox(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                tag = self.both[sheettype]

                html = self.list_page(sheettype, [tag.pk])

                self.assertEqual(checked_sidebar_tags(html), {tag.pk})

    def test_two_tags_in_the_url_pre_check_both(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                chosen = {self.both[sheettype].pk, self.only_first[sheettype].pk}

                html = self.list_page(sheettype, sorted(chosen))

                self.assertEqual(checked_sidebar_tags(html), chosen)

    def test_no_tags_in_the_url_pre_checks_nothing(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                self.assertEqual(checked_sidebar_tags(self.list_page(sheettype)), set())

    def test_an_empty_tags_parameter_pre_checks_nothing(self):
        """`?tags=` is what a page that cleared its filter would leave behind."""
        html = self.list_page("model", [])

        self.assertEqual(checked_sidebar_tags(html), set())

    def test_an_unknown_tag_in_the_url_is_ignored_not_an_error(self):
        """A stale bookmark must render the page, not a 500."""
        html = self.list_page("model", ["no-such-tag"])

        self.assertEqual(checked_sidebar_tags(html), set())

    def test_a_legacy_prefixed_value_pre_checks_nothing(self):
        """The prefix is tolerated where the old links point, and only there.

        Only the CSV download link ever carried it; the list page had no
        `?tags=` at all before this, so there is no legacy list URL to be
        kind to -- and being kind anyway would mean this page could not tell
        a prefixed pk from a real tag whose pk starts with the prefix.
        """
        html = self.list_page("model", ["select_%s" % self.both["model"].pk])

        self.assertEqual(checked_sidebar_tags(html), set())

    def test_a_tag_the_other_sheet_type_uses_pre_checks_nothing_here(self):
        """The filter list is scoped per sheet type; the pre-check follows it."""
        html = self.list_page("model", [self.framework_only.pk])

        self.assertEqual(checked_sidebar_tags(html), set())


class TestTheSelectPrefixIsADomIdOnly(TagFilterUrlTestCase):
    """The prefix is what made the CSV link and the CSV view disagree.

    It survives as an `id` -- the label needs something to point at -- and
    nowhere else. Asserted over the whole rendered page rather than over the
    handler alone, because the mismatch was between two places that never
    appeared in the same diff.
    """

    def test_every_select_prefix_in_the_page_is_an_id(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                html = self.list_page(sheettype, [self.both[sheettype].pk])

                self.assertEqual(
                    len(_SELECT_PREFIX.findall(html)),
                    len(_SELECT_AS_ID.findall(html)),
                )

    def test_the_page_offers_checkboxes_at_all(self):
        """Guards the assertion above from passing on an empty sidebar."""
        html = self.list_page("model")

        self.assertGreater(len(_SELECT_AS_ID.findall(html)), 0)


class TestTheFilteredCsvDownloadReturnsRows(TagFilterUrlTestCase):
    """The defect here was silence: a header row and no error."""

    def test_a_single_tag_returns_the_factsheets_carrying_it(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                rows = self.csv_rows(sheettype, self.both[sheettype].pk)

                self.assertEqual(len(rows), 2)

    def test_two_tags_return_only_factsheets_carrying_both(self):
        """The existing AND semantics, which this must not change."""
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                pks = "%s,%s" % (
                    self.both[sheettype].pk,
                    self.only_first[sheettype].pk,
                )

                rows = self.csv_rows(sheettype, pks)

                self.assertEqual(len(rows), 1)

    def test_an_unfiltered_download_still_returns_every_factsheet(self):
        """The endpoint has machine consumers; the unfiltered case is theirs."""
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                rows = self.csv_rows(sheettype)

                self.assertEqual(len(rows), len(self.corpus[sheettype].factsheets))

    def test_a_legacy_prefixed_link_still_returns_its_rows(self):
        """Links produced by the old page are in bookmarks and in mails.

        Decided explicitly rather than by omission: the CSV view strips a
        leading `select_`, because the alternative leaves those links doing
        the very thing this ticket is fixing -- returning an empty file with
        no error.
        """
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                rows = self.csv_rows(sheettype, "select_%s" % self.both[sheettype].pk)

                self.assertEqual(len(rows), 2)

    def test_a_real_tag_whose_pk_begins_with_the_prefix_is_not_stripped(self):
        """A tag pk is its normalised name, so one can start with the prefix.

        `Tag.get_name_normalized("Select data")` is `select_data`. Stripping
        blindly would filter on `data` instead: a wrong answer with no error,
        which is the class of failure this ticket exists to remove.
        """
        sheets = self.corpus["model"].factsheets
        ambiguous = Tag.objects.create(
            name_normalized="select_data", name="Select data", color=0x111111
        )
        shadowed = Tag.objects.create(
            name_normalized="data", name="data", color=0x222222
        )
        sheets[2].tags.add(ambiguous)
        sheets[3].tags.add(shadowed)
        sheets[4].tags.add(shadowed)

        rows = self.csv_rows("model", ambiguous.pk)

        self.assertEqual(len(rows), 1)

    def test_an_unknown_tag_returns_no_rows_and_no_error(self):
        rows = self.csv_rows("model", "no-such-tag")

        self.assertEqual(rows, [])
