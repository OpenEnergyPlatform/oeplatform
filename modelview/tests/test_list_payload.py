"""What the list page's row payload owes the table that consumes it.

The payload used to be assembled in the template, and its `model_name` and
`tags` keys sat *inside* a loop over the view-property groups -- so they were
emitted once per group: seven times per model factsheet, four times per
framework. Duplicate keys in a JS object literal silently overwrite, which is
why nobody saw 85,092 tag objects go over the wire for 12,156 attachments.

The assertions here are on what the *response* carries, not on the builder's
internals: the builder exists so the list view and the lazy full-payload
endpoint can share one shape, and the shape is only real where the browser
reads it.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

import json
import re

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils.html import escape

from base.tests import TestViewsTestCase
from modelview.helper import (
    FRAMEWORK_VIEW_PROPS,
    MODEL_VIEW_PROPS,
    getClasses,
)
from modelview.list_payload import MAX_WORDS, leaf_fields
from modelview.tests.corpus import seed_corpus

#: The element `json_script` writes the rows into, and the id the page's
#: script reads back.
PAYLOAD_ELEMENT_ID = "factsheet-rows"

_PAYLOAD = re.compile(
    r'<script id="%s" type="application/json">(.*?)</script>' % PAYLOAD_ELEMENT_ID,
    re.DOTALL,
)


#: The test client logs in and out around every request, so a raw query
#: count carries seven `django_session` statements that the view never issues.
#: Filtering by table name keeps the bound on the view's own queries.
_CLIENT_BOOKKEEPING = ("django_session", "SAVEPOINT", "RELEASE SAVEPOINT")


def view_queries(captured):
    """The captured queries the view itself issued."""
    return [
        query["sql"]
        for query in captured.captured_queries
        if not any(noise in query["sql"] for noise in _CLIENT_BOOKKEEPING)
    ]


def _no_duplicate_keys(pairs):
    """A `json.loads` hook that refuses an object carrying a repeated key.

    `dict` silently keeps the last value, exactly as a JS object literal does,
    so parsing normally would hide the very defect this slice removes.
    """
    seen = set()
    for key, _value in pairs:
        if key in seen:
            raise AssertionError("duplicate key in the payload: %r" % (key,))
        seen.add(key)
    return dict(pairs)


def factsheet_name(row):
    """The plain name inside a row's `model_name` cell, which is an anchor."""
    return re.sub(r"<[^>]*>", "", row["model_name"])


class ListPayloadTestCase(TestViewsTestCase):
    """Shared access to the payload the list page actually shipped."""

    def raw_payload(self, sheettype, query=None):
        resp = self.get(
            "modelview:modellist", kwargs={"sheettype": sheettype}, query=query
        )
        html = resp.content.decode("utf-8")
        found = _PAYLOAD.search(html)
        self.assertIsNotNone(
            found, msg="no json_script payload element on the %s list" % sheettype
        )
        return html, found.group(1)

    def payload(self, sheettype, query=None):
        _html, raw = self.raw_payload(sheettype, query)
        return json.loads(raw, object_pairs_hook=_no_duplicate_keys)

    def full_payload(self, sheettype):
        """The complete record, from the lazy endpoint.

        The list page ships only the default columns since the payload became
        page-sized, so every assertion about a non-default field belongs
        here. Same builder either way -- that is the point of the seam.
        """
        resp = self.get("modelview:list-payload", kwargs={"sheettype": sheettype})
        return json.loads(
            resp.content.decode("utf-8"), object_pairs_hook=_no_duplicate_keys
        )

    def rows_by_name(self, sheettype, query=None):
        """The list page's payload, keyed by factsheet name."""
        return {factsheet_name(row): row for row in self.payload(sheettype, query)}

    def full_rows_by_name(self, sheettype):
        """The complete record, keyed by factsheet name."""
        return {factsheet_name(row): row for row in self.full_payload(sheettype)}


class TestPayloadShape(ListPayloadTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.models = seed_corpus(sheettype="model", factsheets=6, corrupted=1)
        cls.frameworks = seed_corpus(sheettype="framework", factsheets=4, corrupted=1)

    def test_one_row_per_model_factsheet(self):
        self.assertEqual(len(self.payload("model")), len(self.models.factsheets))

    def test_one_row_per_framework_factsheet(self):
        self.assertEqual(
            len(self.payload("framework")), len(self.frameworks.factsheets)
        )

    def test_rows_are_in_the_order_the_table_shows_today(self):
        """Unchanged from the template loop: whatever `objects.all()` yields."""
        for sheettype in ("model", "framework"):
            cls, _ = getClasses(sheettype)
            expected = [sheet.model_name for sheet in cls.objects.all()]

            names = [factsheet_name(row) for row in self.payload(sheettype)]
            self.assertEqual(names, expected, msg=sheettype)

    def test_every_key_appears_exactly_once_per_row(self):
        """The whole point of a dict: it cannot carry the duplicate-key bug.

        Asserted on the emitted JSON text rather than on the parsed object,
        because a parsed object has already dropped the duplicates.
        """
        for sheettype in ("model", "framework"):
            self.payload(sheettype)  # the hook raises on a repeated key

    def test_the_full_payload_carries_every_field_the_view_properties_name(self):
        """Which columns the *list* ships is bounded in `test_lazy_payload`."""
        cases = (
            ("model", MODEL_VIEW_PROPS),
            ("framework", FRAMEWORK_VIEW_PROPS),
        )
        for sheettype, props in cases:
            row = self.full_payload(sheettype)[0]

            expected = set(leaf_fields(props)) | {"model_name", "tags"}
            self.assertEqual(set(row), expected, msg=sheettype)

    def test_model_name_links_to_the_factsheet(self):
        cls, _ = getClasses("model")
        sheet = cls.objects.all()[0]

        row = self.payload("model")[0]

        self.assertIn('href="%s"' % sheet.id, row["model_name"])
        self.assertIn(sheet.model_name, row["model_name"])


class TestPayloadTags(ListPayloadTestCase):
    """Every row carries its FULL tag array, and each tag its display colours.

    Not the five the renderer shows: the client-side filter iterates the row's
    whole tag list to decide whether the row matches the active selection, so
    a capped array would silently stop filtering any factsheet with more than
    five tags.
    """

    @classmethod
    def setUpTestData(cls):
        cls.corpus = seed_corpus(sheettype="model", factsheets=4, corrupted=1)

    def test_a_row_carries_all_of_its_tags(self):
        rows = self.rows_by_name("model")

        for sheet in self.corpus.factsheets:
            self.assertEqual(
                len(rows[sheet.model_name]["tags"]),
                sheet.tags.count(),
                msg=sheet.model_name,
            )

    def test_the_corrupted_factsheet_is_not_capped_at_five(self):
        rows = self.payload("model")
        widest = max(len(row["tags"]) for row in rows)

        self.assertEqual(widest, len(self.corpus.tags))

    def test_a_tag_carries_what_the_renderer_and_the_filter_need(self):
        row = max(self.payload("model"), key=lambda r: len(r["tags"]))

        self.assertEqual(
            set(row["tags"][0]), {"pk", "name", "color_hex", "textcolor_hex"}
        )

    def test_the_tag_pks_are_the_ones_the_filter_compares_against(self):
        """Raw pks on both sides -- the one format T5 made canonical."""
        sheet = self.corpus.healthy[0]
        rows = self.rows_by_name("model")

        pks = {tag["pk"] for tag in rows[sheet.model_name]["tags"]}
        self.assertEqual(pks, set(sheet.tags.values_list("pk", flat=True)))


class TestPayloadQueryCount(ListPayloadTestCase):
    """The headline number: 3 queries, flat in the number of factsheets.

    It was `7 x N + 2` -- 2,138 at production's shape -- because the template
    evaluated `model.tags.all` once per view-property group with no prefetch
    anywhere in the view. Locally the prefetch buys no wall time (a query over
    a unix socket is ~0.1 ms), which is exactly why the query count is a bound
    in its own right rather than a proxy for seconds.
    """

    #: The factsheet queryset, its `tags` prefetch, and the sidebar's filter
    #: list. Nothing else, whatever N is.
    EXPECTED_QUERIES = 3

    def assertListQueries(self, sheettype, query=None):
        with CaptureQueriesContext(connection) as captured:
            self.get(
                "modelview:modellist",
                kwargs={"sheettype": sheettype},
                query=query,
            )

        issued = view_queries(captured)
        self.assertEqual(
            len(issued),
            self.EXPECTED_QUERIES,
            msg="%s list issued %d queries:\n%s"
            % (sheettype, len(issued), "\n".join(q[:120] for q in issued)),
        )

    def test_the_model_list_issues_three_queries(self):
        seed_corpus(sheettype="model", factsheets=6, corrupted=1)

        self.assertListQueries("model")

    def test_the_framework_list_issues_three_queries(self):
        seed_corpus(sheettype="framework", factsheets=4, corrupted=1)

        self.assertListQueries("framework")

    def test_the_query_count_does_not_grow_with_the_number_of_factsheets(self):
        for sheettype in ("model", "framework"):
            seed_corpus(sheettype=sheettype, factsheets=3, corrupted=1)
            self.assertListQueries(sheettype)

            seed_corpus(sheettype=sheettype, factsheets=12, corrupted=1)
            self.assertListQueries(sheettype)

    def test_a_filtered_request_costs_the_same(self):
        corpus = seed_corpus(sheettype="model", factsheets=6, corrupted=1)

        self.assertListQueries("model", query={"tags": corpus.tags[0].pk})


class TestPayloadEscaping(ListPayloadTestCase):
    """`json_script`, not `|safe`.

    A field value carrying a closing script tag ends the script element early
    when the payload is a JS literal: everything after it lands in the
    document as markup and the table never initialises. `json_script` escapes
    `<`, `>` and `&` to their unicode escapes, so no value can close the
    element.
    """

    BREAKOUT = "</script><script>window.pwned=1</script>"

    @classmethod
    def setUpTestData(cls):
        corpus = seed_corpus(sheettype="model", factsheets=2, corrupted=0)
        cls.sheet = corpus.factsheets[0]
        cls.sheet.primary_purpose = cls.BREAKOUT
        cls.sheet.save()

    def test_no_markup_survives_inside_the_payload_element(self):
        """`json_script` escapes `<`, `>` and `&` to their unicode escapes.

        So the payload element carries no tag of any kind: nothing in it can
        close the element early, and nothing after it is parsed as markup.
        Both layers show up here -- the anchor the builder writes for
        `model_name` arrives as `\\u003Ca`, and the field value, already
        HTML-escaped as `&lt;`, arrives with that ampersand escaped in turn.
        """
        _html, raw = self.raw_payload("model")

        self.assertNotIn("<", raw)
        self.assertNotIn(">", raw)
        self.assertIn("\\u003Ca href=", raw)
        self.assertIn("\\u0026lt;/script\\u0026gt;", raw)

    def test_the_value_arrives_as_text_not_as_markup(self):
        """Two escapes, two jobs -- and the cell needs its own.

        `json_script` protects the transport: nothing in a value can close the
        script element. It does NOT protect the cell, because the table writes
        every cell through `innerHTML` -- so the value is HTML-escaped in the
        builder as well, exactly as the retired template filter did. Only its
        JS-literal quoting is obsolete.
        """
        rows = self.rows_by_name("model")

        self.assertEqual(
            rows[self.sheet.model_name]["primary_purpose"], escape(self.BREAKOUT)
        )

    def test_a_field_carrying_an_onerror_image_cannot_execute(self):
        """The live risk: any logged-in account can edit any factsheet."""
        self.sheet.comment_on_geo_resolution = '<img src=x onerror="p=1">'
        self.sheet.save()

        row = self.rows_by_name("model")[self.sheet.model_name]

        self.assertNotIn("<img", row["comment_on_geo_resolution"])
        self.assertIn("&lt;img", row["comment_on_geo_resolution"])

    def test_the_entries_of_an_array_field_are_escaped_too(self):
        """Through the full payload: array fields are not default columns."""
        self.sheet.institutions = ["<b>bold</b>", "plain"]
        self.sheet.save()

        rows = self.full_rows_by_name("model")

        self.assertEqual(
            rows[self.sheet.model_name]["institutions"],
            ["&lt;b&gt;bold&lt;/b&gt;", "plain"],
        )

    def test_a_model_name_carrying_markup_is_escaped_inside_the_link(self):
        """`model_name` is the one value the payload wraps in HTML itself."""
        self.sheet.model_name = 'Break "out" <b>now</b>'
        self.sheet.save()

        row = [r for r in self.payload("model") if "Break" in r["model_name"]][0]

        self.assertNotIn("<b>", row["model_name"])
        self.assertIn("&lt;b&gt;", row["model_name"])


class TestPayloadTruncation(ListPayloadTestCase):
    """The 12-word truncation moved into the builder and stays.

    It costs nothing (3.43 -> 3.28 MB at production's shape) and dropping it
    would silently change what every cell of the table displays.
    """

    @classmethod
    def setUpTestData(cls):
        corpus = seed_corpus(sheettype="model", factsheets=2, corrupted=0)
        cls.sheet = corpus.factsheets[0]
        cls.sheet.primary_purpose = " ".join("word%d" % i for i in range(30))
        cls.sheet.institutions = [" ".join("inst%d" % i for i in range(30))]
        cls.sheet.comment_on_geo_resolution = "short enough"
        cls.sheet.save()

    def _row(self):
        return [
            row
            for row in self.payload("model")
            if self.sheet.model_name in row["model_name"]
        ][0]

    def test_a_long_string_is_truncated_to_twelve_words_plus_an_ellipsis(self):
        value = self._row()["primary_purpose"]

        self.assertEqual(value.split(" ")[: MAX_WORDS + 1][-1], "...")
        self.assertEqual(len(value.split(" ")), MAX_WORDS + 1)

    def test_a_short_string_is_untouched(self):
        self.assertEqual(self._row()["comment_on_geo_resolution"], "short enough")

    def test_the_entries_of_an_array_field_are_truncated_too(self):
        """Through the full payload: array fields are not default columns."""
        entry = self.full_rows_by_name("model")[self.sheet.model_name]["institutions"][
            0
        ]

        self.assertEqual(len(entry.split(" ")), MAX_WORDS + 1)

    def test_newlines_are_stripped(self):
        self.sheet.comment_on_geo_resolution = "one\ntwo\r\nthree"
        self.sheet.save()

        self.assertEqual(self._row()["comment_on_geo_resolution"], "onetwothree")


class TestTheTableWiringSurvives(ListPayloadTestCase):
    """The payload block is rewritten around code that must not be lost.

    The tag filter's logic is a real ES module since T5, imported by a
    `<script type="module">` and reached from a DataTables search extension.
    Both live in the same template block as the payload, so a slice that
    rewrites that block can drop them without any Python test noticing.
    """

    @classmethod
    def setUpTestData(cls):
        seed_corpus(sheettype="model", factsheets=2, corrupted=0)

    def test_the_filter_module_is_still_imported(self):
        resp = self.get("modelview:modellist", kwargs={"sheettype": "model"})
        html = resp.content.decode("utf-8")

        self.assertIn("modelview/tag_filter.js", html)
        self.assertIn('type="module"', html)

    def test_the_search_extension_still_calls_the_filter(self):
        resp = self.get("modelview:modellist", kwargs={"sheettype": "model"})
        html = resp.content.decode("utf-8")

        self.assertIn("rowMatchesTags", html)
        self.assertIn("checkedTagValues", html)
