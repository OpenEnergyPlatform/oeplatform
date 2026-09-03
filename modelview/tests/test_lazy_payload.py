"""The initial payload is page-sized; the other columns arrive on demand.

The pager was always real DataTables paging -- but it paged a payload that had
already been queried, rendered and shipped whole: 305 factsheets x 171 fields,
a 20.1 MB page, to display eight columns. The list now ships those eight for
every row and serves the rest from one endpoint, fetched once.

The trigger for that fetch is a browser property, and the "once" half of it is
browser state; both live in `modelview/static/modelview/lazy_payload.js` with
their own vitest suite. What is asserted here is what the server sends.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

import json
import re

from django.db import connection
from django.test.utils import CaptureQueriesContext

from modelview.helper import (
    FRAMEWORK_DEFAULT_COLUMNS,
    FRAMEWORK_VIEW_PROPS,
    MODEL_DEFAULT_COLUMNS,
    MODEL_VIEW_PROPS,
)
from modelview.list_payload import leaf_fields
from modelview.tests.corpus import seed_corpus
from modelview.tests.test_list_payload import (
    ListPayloadTestCase,
    factsheet_name,
    view_queries,
)

#: How many model fields each sheet type's view properties name.
MODEL_LEAF_FIELDS = 171
FRAMEWORK_LEAF_FIELDS = 41

#: One DataTables column definition in the rendered page.
_COLUMN_DEFINITION = re.compile(r"\{data: '[^']*'[^}]*\}")


class TestTheInitialPayloadIsPageSized(ListPayloadTestCase):
    """Eight keys per row for models, five for frameworks -- and no more.

    `MODEL_DEFAULT_COLUMNS` already names `model_name` and `tags`, so the
    "eight default columns plus tags" the ticket asks for is eight keys: six
    leaf fields and those two. 1.32 MB at production's shape against 20.1 MB,
    and 0.16 MB once the corrupted factsheets are repaired -- half of one
    25-row page of the full record, so the payload costs less than a page
    without paginating at all.
    """

    @classmethod
    def setUpTestData(cls):
        seed_corpus(sheettype="model", factsheets=4, corrupted=1)
        seed_corpus(sheettype="framework", factsheets=3, corrupted=1)

    def test_a_model_row_carries_the_default_columns_and_nothing_else(self):
        row = self.payload("model")[0]

        self.assertEqual(set(row), set(MODEL_DEFAULT_COLUMNS))
        self.assertEqual(len(row), 8)

    def test_a_framework_row_carries_the_default_columns_and_nothing_else(self):
        row = self.payload("framework")[0]

        self.assertEqual(set(row), set(FRAMEWORK_DEFAULT_COLUMNS))
        self.assertEqual(len(row), 5)

    def test_the_initial_payload_carries_no_lazy_field(self):
        """The regression this bound exists for: 171 fields creeping back."""
        cases = (
            ("model", MODEL_VIEW_PROPS, MODEL_DEFAULT_COLUMNS),
            ("framework", FRAMEWORK_VIEW_PROPS, FRAMEWORK_DEFAULT_COLUMNS),
        )
        for sheettype, props, defaults in cases:
            lazy = set(leaf_fields(props)) - set(defaults)
            self.assertTrue(lazy, msg=sheettype)

            for row in self.payload(sheettype):
                self.assertEqual(set(row) & lazy, set(), msg=sheettype)

    def test_every_row_still_carries_its_full_tag_array(self):
        """The tag filter reads `row.tags`, so trimming columns must not trim
        tags -- a capped array silently stops filtering wide factsheets."""
        widest = max(len(row["tags"]) for row in self.payload("model"))

        self.assertGreater(widest, 200)


class TestTheFullPayloadEndpoint(ListPayloadTestCase):
    """The other 165 columns, on one URL, in the list's own row order."""

    @classmethod
    def setUpTestData(cls):
        cls.models = seed_corpus(sheettype="model", factsheets=4, corrupted=1)
        cls.frameworks = seed_corpus(sheettype="framework", factsheets=3, corrupted=1)

    def rows(self, sheettype):
        resp = self.get("modelview:list-payload", kwargs={"sheettype": sheettype})
        self.assertEqual(resp["Content-Type"], "application/json")
        return json.loads(resp.content.decode("utf-8"))

    def test_it_returns_every_field_the_view_properties_name(self):
        cases = (
            ("model", MODEL_VIEW_PROPS, MODEL_LEAF_FIELDS),
            ("framework", FRAMEWORK_VIEW_PROPS, FRAMEWORK_LEAF_FIELDS),
        )
        for sheettype, props, count in cases:
            names = leaf_fields(props)
            # Absolutely, because the key set below is derived with the same
            # helper the view uses: a `leaf_fields` that silently dropped a
            # group would otherwise agree with itself.
            self.assertEqual(len(names), count, msg=sheettype)

            row = self.full_payload(sheettype)[0]

            self.assertEqual(
                set(row), set(names) | {"model_name", "tags"}, msg=sheettype
            )

    def test_its_rows_match_the_list_in_number_and_order(self):
        """The table replaces its rows wholesale, so a different order would
        silently reshuffle the page under the reader."""
        for sheettype in ("model", "framework"):
            listed = [factsheet_name(row) for row in self.payload(sheettype)]

            fetched = [factsheet_name(row) for row in self.full_payload(sheettype)]

            self.assertEqual(fetched, listed, msg=sheettype)

    def test_it_carries_the_full_tag_array_too(self):
        widest = max(len(row["tags"]) for row in self.full_payload("model"))

        self.assertEqual(widest, len(self.models.tags))

    def test_it_costs_two_queries_whatever_the_corpus_size(self):
        """The rows and their tags. It renders no sidebar, so it does not pay
        for the filter list the list page's third query buys."""
        for sheettype in ("model", "framework"):
            self.assertPayloadQueries(sheettype, 2)

            seed_corpus(sheettype=sheettype, factsheets=8, corrupted=0)

            self.assertPayloadQueries(sheettype, 2)

    def assertPayloadQueries(self, sheettype, expected):
        with CaptureQueriesContext(connection) as captured:
            self.full_payload(sheettype)

        self.assertEqual(len(view_queries(captured)), expected, msg=sheettype)

    def test_an_unknown_sheettype_is_not_found(self):
        resp = self.client.get("/factsheets/scenarios/payload/")

        self.assertEqual(resp.status_code, 404)


class TestTheColumnDefinitions(ListPayloadTestCase):
    """`defaultContent` on every definition, or the first draw throws.

    Handing 173 column definitions rows that carry eight keys raises three
    DataTables errors on the first draw, because the table builds a row cache
    across every definition, visible or not. With `defaultContent` it is zero,
    at no cost -- and silent if forgotten, which is why it is asserted.
    """

    @classmethod
    def setUpTestData(cls):
        seed_corpus(sheettype="model", factsheets=2, corrupted=0)
        seed_corpus(sheettype="framework", factsheets=2, corrupted=0)

    def definitions(self, sheettype):
        resp = self.get("modelview:modellist", kwargs={"sheettype": sheettype})
        html = resp.content.decode("utf-8")
        found = _COLUMN_DEFINITION.findall(html)
        self.assertTrue(found, msg="no column definitions on the %s list" % sheettype)
        return found

    def test_every_column_definition_carries_default_content(self):
        for sheettype in ("model", "framework"):
            for definition in self.definitions(sheettype):
                self.assertIn("defaultContent", definition, msg=definition)

    def test_there_is_one_definition_per_field_plus_name_and_tags(self):
        cases = (
            ("model", MODEL_VIEW_PROPS),
            ("framework", FRAMEWORK_VIEW_PROPS),
        )
        for sheettype, props in cases:
            self.assertEqual(
                len(self.definitions(sheettype)),
                len(leaf_fields(props)) + 2,
                msg=sheettype,
            )


class TestTheLazyWiringSurvives(ListPayloadTestCase):
    """The page must actually reach the endpoint, and know what it already has.

    All three are one-line losses in a template rewrite, and all three fail
    silently: without the module the toggle throws, without the endpoint URL
    the fetch 404s, and without the initial column list every toggle refetches.
    """

    @classmethod
    def setUpTestData(cls):
        seed_corpus(sheettype="model", factsheets=2, corrupted=0)

    def test_the_page_imports_the_lazy_payload_module(self):
        resp = self.get("modelview:modellist", kwargs={"sheettype": "model"})
        html = resp.content.decode("utf-8")

        self.assertIn("modelview/lazy_payload.js", html)

    def test_the_page_carries_the_endpoint_url(self):
        resp = self.get("modelview:modellist", kwargs={"sheettype": "model"})
        html = resp.content.decode("utf-8")

        self.assertIn("/factsheets/models/payload/", html)

    def test_the_page_tells_the_browser_which_columns_it_already_has(self):
        resp = self.get("modelview:modellist", kwargs={"sheettype": "model"})
        html = resp.content.decode("utf-8")

        found = re.search(
            r'<script id="factsheet-initial-columns" type="application/json">'
            r"(.*?)</script>",
            html,
            re.DOTALL,
        )
        self.assertIsNotNone(found)
        self.assertEqual(set(json.loads(found.group(1))), set(MODEL_DEFAULT_COLUMNS))
