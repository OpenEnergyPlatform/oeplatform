"""
SPDX-FileCopyrightText: none
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import csv
import io

from base.tests import TestViewsTestCase
from modelview.helper import getClasses
from modelview.tests.corpus import CORRUPT_THRESHOLD, seed_corpus


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
        cls.models = seed_corpus(sheettype="model", factsheets=6, corrupted=1)
        cls.frameworks = seed_corpus(sheettype="framework", factsheets=3, corrupted=1)

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
        cls.models = seed_corpus(sheettype="model", factsheets=6, corrupted=1)
        cls.frameworks = seed_corpus(sheettype="framework", factsheets=3, corrupted=1)

    def _rows(self, sheettype):
        resp = self.get("modelview:download", kwargs={"sheettype": sheettype})
        body = resp.content.decode("utf-8")
        return list(csv.reader(io.StringIO(body)))

    def test_returns_one_row_per_model_factsheet_plus_a_header(self):
        rows = self._rows("model")

        self.assertEqual(len(rows), 6 + 1)

    def test_returns_one_row_per_framework_factsheet_plus_a_header(self):
        rows = self._rows("framework")

        self.assertEqual(len(rows), 3 + 1)

    def test_header_carries_the_identifying_columns(self):
        header = self._rows("model")[0]

        self.assertIn("id", header)
        self.assertIn("model_name", header)
        self.assertIn("acronym", header)

    def test_the_tags_column_carries_no_tags(self):
        """A documented defect, pinned so that fixing it is deliberate.

        `ManyToManyField` does have an `attname`, so the header-building code
        emits a `tags` column -- but the row-building code hands the csv writer
        the related *manager*, whose `__str__` is the constant
        `dataedit.Tag.None`. So every cell of that column is the same string,
        for every factsheet, in both sheet types. It is stable rather than
        random, which is why it has never been noticed.

        Whoever gives this column real content (T5 touches this view, and the
        map has an open question about whether the CSV is the documented bulk
        interface) should change this test on purpose.
        """
        rows = self._rows("model")
        header, body = rows[0], rows[1:]

        self.assertIn("tags", header)
        tags_column = header.index("tags")
        cells = {row[tags_column] for row in body}
        self.assertEqual(cells, {"dataedit.Tag.None"})

    def test_rows_are_ordered_by_pk(self):
        rows = self._rows("model")
        header, body = rows[0], rows[1:]
        id_column = header.index("id")

        ids = [int(row[id_column]) for row in body]
        self.assertEqual(ids, sorted(ids))


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

    def test_an_empty_submit_creates_no_factsheet(self):
        cls, _ = getClasses("model")
        before = cls.objects.count()

        self.post(
            "modelview:modeladd", kwargs={"sheettype": "model"}, data={}, logged_in=True
        )

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
