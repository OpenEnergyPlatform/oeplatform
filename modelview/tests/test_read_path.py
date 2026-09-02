"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import csv
import io

from django.db import connection
from django.test.utils import CaptureQueriesContext

from base.tests import TestViewsTestCase
from modelview.helper import getClasses
from modelview.tests.corpus import CORRUPT_THRESHOLD, seed_corpus

#: Big enough that a per-factsheet query shows up as a count proportional to
#: N rather than as noise, small enough to stay CI-cheap. The read-path bounds
#: the later slices add (a flat query count, a page-sized payload) need a
#: corpus that can tell O(1) from O(N).
MODEL_FACTSHEETS = 25
FRAMEWORK_FACTSHEETS = 12


class TestCorpusFactory(TestViewsTestCase):
    """The corpus must reproduce the shape the later slices assert against.

    Every read-path bound in this app's regression net is asserted against a
    seeded corpus, so the corpus itself needs assertions: a factory that
    silently seeded no corrupted factsheets would make the cleanup command's
    test pass for the wrong reason.
    """

    def test_seeds_the_requested_number_of_factsheets_and_tags(self):
        corpus = seed_corpus(factsheets=8, tags=210, corrupted=1)

        self.assertEqual(len(corpus.factsheets), 8)
        self.assertEqual(len(corpus.tags), 210)

    def test_seeds_exactly_the_requested_number_of_corrupted_factsheets(self):
        corpus = seed_corpus(factsheets=8, tags=210, corrupted=3)

        self.assertEqual(len(corpus.corrupted), 3)
        self.assertEqual(len(corpus.healthy), 5)

    def test_corrupted_factsheets_are_over_the_detection_threshold(self):
        """`tags > 200` is production's detection rule -- see WF-03's census.

        A corrupted factsheet carries a snapshot of the whole tag table, so the
        vocabulary has to be larger than the threshold for the corpus to be
        able to express corruption at all.
        """
        corpus = seed_corpus(factsheets=8, tags=210, corrupted=2)

        for sheet in corpus.corrupted:
            self.assertGreater(sheet.tags.count(), CORRUPT_THRESHOLD)

    def test_healthy_factsheets_are_well_under_the_threshold(self):
        corpus = seed_corpus(factsheets=8, tags=210, corrupted=2, healthy_tags=3)

        for sheet in corpus.healthy:
            self.assertEqual(sheet.tags.count(), 3)

    def test_refuses_to_seed_corruption_it_cannot_express(self):
        """A vocabulary at or under the threshold cannot produce a corruption.

        The ticket originally asked for ~50 tags. A corrupted factsheet
        attaches the whole vocabulary, so at 50 tags every factsheet would sit
        under the 200-tag rule and the cleanup command's test would pass
        without ever seeing corruption.
        """
        with self.assertRaises(ValueError):
            seed_corpus(factsheets=8, tags=50, corrupted=2)

    def test_counts_the_edges_it_created(self):
        """The tag *edge* count is what the list page's cost is super-linear in."""
        corpus = seed_corpus(factsheets=8, tags=210, corrupted=2, healthy_tags=3)

        self.assertEqual(corpus.edges, 2 * 210 + 6 * 3)

    def test_seeds_frameworks_too(self):
        corpus = seed_corpus(sheettype="framework", factsheets=4, tags=210, corrupted=1)

        cls, _ = getClasses("framework")
        self.assertEqual(cls.objects.count(), 4)
        self.assertEqual(len(corpus.corrupted), 1)

    def test_the_two_sheet_types_do_not_collide(self):
        seed_corpus(sheettype="model", factsheets=4, tags=210, corrupted=1)
        seed_corpus(sheettype="framework", factsheets=3, tags=210, corrupted=1)

        model_cls, _ = getClasses("model")
        framework_cls, _ = getClasses("framework")
        self.assertEqual(model_cls.objects.count(), 4)
        self.assertEqual(framework_cls.objects.count(), 3)


class TestListPageRenders(TestViewsTestCase):
    """The list page must render against a corpus carrying corruption.

    This is the assertion the later read-path slices sharpen: T4 bounds the
    filter list, T6 the query count, T7 the payload's columns.
    """

    @classmethod
    def setUpTestData(cls):
        seed_corpus(sheettype="model", factsheets=MODEL_FACTSHEETS, corrupted=2)
        seed_corpus(sheettype="framework", factsheets=FRAMEWORK_FACTSHEETS, corrupted=1)

    def test_model_list_renders(self):
        self.get("modelview:modellist", kwargs={"sheettype": "model"})

    def test_framework_list_renders(self):
        self.get("modelview:modellist", kwargs={"sheettype": "framework"})


class TestCsvDownload(TestViewsTestCase):
    """What the CSV download owes any consumer.

    It is the only cheap, complete, machine-readable view of these rows
    (0.336 s on production against ~400 s for the HTML list), and it had no
    test at all. T5 adds the tag-filtered case, which today silently returns a
    header-only file.
    """

    @classmethod
    def setUpTestData(cls):
        cls.models = seed_corpus(
            sheettype="model", factsheets=MODEL_FACTSHEETS, corrupted=2
        )
        cls.frameworks = seed_corpus(
            sheettype="framework", factsheets=FRAMEWORK_FACTSHEETS, corrupted=1
        )

    def _rows(self, sheettype):
        resp = self.get("modelview:download", kwargs={"sheettype": sheettype})
        body = resp.content.decode("utf-8")
        return list(csv.reader(io.StringIO(body)))

    def test_returns_one_row_per_model_factsheet_plus_a_header(self):
        rows = self._rows("model")

        self.assertEqual(len(rows), len(self.models.factsheets) + 1)

    def test_returns_one_row_per_framework_factsheet_plus_a_header(self):
        rows = self._rows("framework")

        self.assertEqual(len(rows), len(self.frameworks.factsheets) + 1)

    def test_the_model_header_carries_the_identifying_columns(self):
        header = self._rows("model")[0]

        self.assertIn("id", header)
        self.assertIn("model_name", header)
        self.assertIn("acronym", header)

    def test_the_framework_header_carries_the_identifying_columns(self):
        header = self._rows("framework")[0]

        self.assertIn("id", header)
        self.assertIn("model_name", header)

    def test_the_header_is_stable_and_free_of_duplicates(self):
        """Stable in the sense a consumer needs: same columns, same order.

        Asserted as a property rather than as a snapshot, so that adding a
        field to a factsheet -- legitimate change -- does not fail, while a
        column emitted twice or in a shifting order does.
        """
        for sheettype in ("model", "framework"):
            first = self._rows(sheettype)[0]
            second = self._rows(sheettype)[0]

            self.assertEqual(first, second, msg=sheettype)
            self.assertEqual(len(first), len(set(first)), msg=sheettype)

    def test_rows_are_ordered_by_pk(self):
        rows = self._rows("model")
        header, body = rows[0], rows[1:]
        id_column = header.index("id")

        ids = [int(row[id_column]) for row in body]
        self.assertEqual(ids, sorted(ids))

    def test_the_query_count_does_not_grow_with_the_number_of_factsheets(self):
        """The CSV's decisive property, and the map's decisive contrast.

        This endpoint returns the same rows as the list page through the same
        ORM with no template, in 0.336 s against ~400 s. It does so because
        its cost is flat in N. The list page's own bound belongs to T6, which
        takes it from `7 x N + 2` to 3; this asserts that the surface which
        measures such a bound works, on an invariant that already holds.
        """
        with CaptureQueriesContext(connection) as before:
            self._rows("model")

        seed_corpus(sheettype="model", factsheets=10, corrupted=0)

        with CaptureQueriesContext(connection) as after:
            rows = self._rows("model")

        self.assertEqual(len(rows), len(self.models.factsheets) + 10 + 1)
        self.assertEqual(len(after), len(before))

    def test_the_tags_column_is_a_constant_known_defect(self):
        """A characterisation test: it records a defect, it does not bless it.

        `ManyToManyField` does have an `attname`, so the header-building code
        emits a `tags` column -- but the row-building code hands the csv writer
        the related *manager*, whose `__str__` is the constant
        `dataedit.Tag.None`. So every cell of that column is the same string,
        for every factsheet, in both sheet types. It is stable rather than
        random, which is why it has never been noticed.

        Unlike everything else in this file, this assertion is expected to
        change: whoever gives the column real content -- T5 touches this view,
        and the map has an open question about whether the CSV is the
        documented bulk interface -- should rewrite this test on purpose,
        rather than discover the behaviour in production.
        """
        rows = self._rows("model")
        header, body = rows[0], rows[1:]

        self.assertIn("tags", header)
        tags_column = header.index("tags")
        cells = {row[tags_column] for row in body}
        self.assertEqual(cells, {"dataedit.Tag.None"})


class TestWriteSeamHelpers(TestViewsTestCase):
    """Exercise the POST and DELETE seams the write-path slices assert through.

    The shared base test case had a `get()` helper and nothing else, so this
    app -- and every other app in the repository -- had no POST coverage at
    all. Both assertions below are true today and must stay true: T3 rewrites
    the save path, T2 hardens the delete path.
    """

    @classmethod
    def setUpTestData(cls):
        cls.corpus = seed_corpus(sheettype="model", factsheets=2, corrupted=0)

    def test_an_empty_submit_reaches_the_view_and_creates_no_factsheet(self):
        """Both halves matter.

        "No factsheet was created" is equally true of a request that never
        reached the view, so the status and the template are asserted too: a
        login redirect would be a 302, and only the add view renders that
        template.
        """
        cls, _ = getClasses("model")
        before = cls.objects.count()

        resp = self.post(
            "modelview:modeladd",
            kwargs={"sheettype": "model"},
            data={},
            logged_in=True,
            expect_status=200,
        )

        self.assertTemplateUsed(resp, "modelview/editmodel.html")
        self.assertEqual(cls.objects.count(), before)

    def test_an_anonymous_delete_is_redirected_to_login(self):
        cls, _ = getClasses("model")
        sheet = self.corpus.factsheets[0]

        self.delete(
            "modelview:delete-factsheet",
            kwargs={"sheettype": "model", "pk": sheet.pk},
            expect_status=302,
        )

        self.assertTrue(cls.objects.filter(pk=sheet.pk).exists())
