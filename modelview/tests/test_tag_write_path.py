"""The factsheet write path: tags, the full-form round trip, and the log line.

This app had no POST coverage at all before this module (`test_views.py` is
GET-only), and `processPost` -- the helper every factsheet submit goes
through -- had never been tested. That is how the tag editor could attach the
whole vocabulary for ten months, and how the array-field serialisation could
silently drop every entry past the ninth for two months.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re

from django.db import connection
from django.test.utils import CaptureQueriesContext

from base.tests import TestViewsTestCase
from modelview.helper import getClasses
from modelview.tests.corpus import seed_corpus
from modelview.tests.form_data import as_post_data, form_values
from modelview.tests.html import checked_values, offered_values

SHEETTYPES = ("model", "framework")

#: The tag selector's checkboxes, which post one multi-valued `tags` field.
TAG_CHECKBOX = "tag-checkbox"


def offered_tag_pks(html: str) -> list[str]:
    return offered_values(html, TAG_CHECKBOX)


def checked_tag_pks(html: str) -> set[str]:
    return checked_values(html, TAG_CHECKBOX)


def current_tag_pills(html: str) -> list[str]:
    """The tag names shown in the "Current tags" block, in render order."""
    block = re.search(r'<span id="current-tags">(.*?)</span>', html, re.DOTALL)
    return re.findall(r">([^<>]+)</a>", block.group(1)) if block else []


class FactsheetWriteTestCase(TestViewsTestCase):
    """A small corpus of both sheet types over one shared tag vocabulary."""

    def setUp(self):
        self.corpus = {
            t: seed_corpus(
                sheettype=t, factsheets=3, tags=210, corrupted=0, healthy_tags=0
            )
            for t in SHEETTYPES
        }

    def sheet(self, sheettype, index=0):
        return self.corpus[sheettype].factsheets[index]

    def vocabulary(self, sheettype):
        return self.corpus[sheettype].tags

    def edit_page(self, sheettype, pk):
        resp = self.get(
            "modelview:edit",
            kwargs={"sheettype": sheettype, "pk": pk},
            logged_in=True,
        )
        return resp.content.decode("utf-8")

    def submit(self, sheettype, sheet, values=None, tags=None, expect_status=None):
        """POST a complete factsheet update, with `tags` as raw pks."""
        if values is None:
            values = form_values(sheettype, model_name=sheet.model_name)
        data = as_post_data(values)
        if tags is not None:
            data["tags"] = list(tags)
        return self.post(
            "modelview:update",
            data=data,
            kwargs={"sheettype": sheettype, "pk": sheet.pk},
            logged_in=True,
            expect_status=expect_status,
        )


class TestTheEditFormPreChecksOnlyTheFactsheetsOwnTags(FactsheetWriteTestCase):
    """#2385 / #2381: the edit view passed `Tag.objects.all()` as `tags`, and
    the widget rendered every one of them `checked`. Saving then attached the
    lot.
    """

    def assert_checked(self, sheettype, html, expected):
        """`expected` boxes checked, out of the whole vocabulary offered.

        The second half is not decoration: a widget that stopped emitting tag
        checkboxes altogether would satisfy "nothing is pre-checked" while
        making the editor useless, so every pre-check assertion states what it
        counted.
        """
        self.assertEqual(len(offered_tag_pks(html)), len(self.vocabulary(sheettype)))
        self.assertEqual(checked_tag_pks(html), expected)

    def test_a_factsheet_with_no_tags_pre_checks_nothing(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                sheet = self.sheet(sheettype)
                sheet.tags.clear()

                html = self.edit_page(sheettype, sheet.pk)

                self.assert_checked(sheettype, html, set())

    def test_a_factsheet_with_two_tags_pre_checks_exactly_those_two(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                sheet = self.sheet(sheettype)
                chosen = self.vocabulary(sheettype)[:2]
                sheet.tags.set(chosen)

                html = self.edit_page(sheettype, sheet.pk)

                self.assert_checked(sheettype, html, {tag.pk for tag in chosen})

    def test_the_add_form_pre_checks_nothing(self):
        """A brand-new factsheet starts untagged, and is offered every tag."""
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                resp = self.get(
                    "modelview:modeladd",
                    kwargs={"sheettype": sheettype},
                    logged_in=True,
                )

                self.assert_checked(sheettype, resp.content.decode("utf-8"), set())


class TestSavingAttachesExactlyWhatWasSelected(FactsheetWriteTestCase):

    def test_selecting_three_tags_attaches_exactly_three(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                sheet = self.sheet(sheettype)
                chosen = self.vocabulary(sheettype)[:3]

                self.submit(sheettype, sheet, tags=[t.pk for t in chosen])

                self.assertEqual(
                    set(sheet.tags.values_list("pk", flat=True)),
                    {t.pk for t in chosen},
                )

    def test_saving_with_no_tags_selected_leaves_none(self):
        """The widget is inside the one form, so "nothing posted" is genuinely
        "nothing selected" -- no sentinel field is needed to tell the two
        apart.
        """
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                sheet = self.sheet(sheettype)
                sheet.tags.set(self.vocabulary(sheettype)[:3])

                self.submit(sheettype, sheet, tags=[])

                self.assertEqual(sheet.tags.count(), 0)

    def test_saving_twice_leaves_the_tags_unchanged(self):
        """The unconditional `tags.clear()` made this fail for any submit that
        did not carry the widget.
        """
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                sheet = self.sheet(sheettype)
                chosen = [t.pk for t in self.vocabulary(sheettype)[:4]]

                self.submit(sheettype, sheet, tags=chosen)
                self.submit(sheettype, sheet, tags=chosen)

                self.assertEqual(
                    set(sheet.tags.values_list("pk", flat=True)), set(chosen)
                )

    def test_a_tag_that_does_not_exist_is_a_validation_error_not_a_crash(self):
        sheettype = "model"
        sheet = self.sheet(sheettype)
        sheet.tags.set(self.vocabulary(sheettype)[:2])

        resp = self.submit(sheettype, sheet, tags=["no-such-tag"])

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(sheet.tags.count(), 2)

    def test_the_save_does_not_issue_a_query_per_selected_tag(self):
        """The old path ran one `Tag.objects.get()` per checked box -- ~1,600
        queries on a corrupted submit, the reported "veeery long on submit
        all". `save_m2m()` costs the same handful of statements either way.

        The bound is a *comparison* between a small and a large selection, not
        a magic number: what must never come back is growth with the number of
        tags selected.
        """
        sheettype = "model"
        vocabulary = self.vocabulary(sheettype)

        # One warm-up submit first: the session and content-type lookups a
        # request makes are cached per test client, so the very first POST
        # costs ten queries the next one does not, and that noise is larger
        # than the effect being measured.
        self.count_queries(sheettype, self.sheet(sheettype, 0), vocabulary[:1])

        few = self.count_queries(sheettype, self.sheet(sheettype, 0), vocabulary[:3])
        many = self.count_queries(sheettype, self.sheet(sheettype, 1), vocabulary[:60])

        self.assertEqual(many, few)

    def count_queries(self, sheettype, sheet, tags):
        with CaptureQueriesContext(connection) as ctx:
            self.submit(sheettype, sheet, tags=[t.pk for t in tags])
        return len(ctx.captured_queries)


class TestTheFullFormRoundTrip(FactsheetWriteTestCase):
    """`processPost` rewritten: every field must survive a submit unchanged.

    This is the first honest net the write path has had. Its risk concentrates
    in the array-field serialisation, which lost every entry past the ninth in
    `4afa9ff8e` and shipped that way.
    """

    def assert_round_trip(self, sheettype, values):
        sheet = self.sheet(sheettype)
        values = dict(values, model_name=sheet.model_name)
        if "license" in values:
            # `FSAddView.post` blanks `license_other_text` unless the licence
            # is "Other", so any other pick would make this test assert the
            # view's own rule wrong rather than the helper's fidelity.
            values["license"] = "Other"

        self.submit(sheettype, sheet, values=values, tags=[])

        cls, _ = getClasses(sheettype)
        reloaded = cls.objects.get(pk=sheet.pk)
        for name, expected in sorted(values.items()):
            with self.subTest(field=name):
                self.assertEqual(getattr(reloaded, name), expected)

    def test_every_field_survives_a_round_trip(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                self.assert_round_trip(
                    sheettype, form_values(sheettype, model_name="unused")
                )

    def test_an_array_field_with_twelve_entries_survives_in_order(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                entries = ["author %02d" % i for i in range(12)]
                values = form_values(sheettype, model_name="unused")
                values["authors"] = entries

                self.assert_round_trip(sheettype, values)


class TestTheInvalidFormPathKeepsTheSelection(FactsheetWriteTestCase):
    """A missing required field elsewhere must not cost the user their tags."""

    def test_a_failed_submit_re_renders_the_submitted_tag_selection(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                sheet = self.sheet(sheettype)
                chosen = [t.pk for t in self.vocabulary(sheettype)[:3]]
                values = form_values(sheettype, model_name=sheet.model_name)
                values["contact_email"] = []  # required, so the form fails

                resp = self.submit(sheettype, sheet, values=values, tags=chosen)

                self.assertEqual(resp.status_code, 200)
                self.assertEqual(
                    checked_tag_pks(resp.content.decode("utf-8")), set(chosen)
                )


class TestTheTagEditorsControls(FactsheetWriteTestCase):
    """What #2385 asked for beyond the fix: a way out, and a visible count."""

    def test_the_editor_offers_remove_all_tags(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                html = self.edit_page(sheettype, self.sheet(sheettype).pk)

                self.assertIn("remove-all-tags", html)

    def test_the_tags_tab_carries_a_selected_count(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                sheet = self.sheet(sheettype)
                sheet.tags.set(self.vocabulary(sheettype)[:2])

                html = self.edit_page(sheettype, sheet.pk)

                self.assertIn("tag-selected-count", html)
                self.assertRegex(html, r'id="tag-selected-count"[^>]*>\s*2\s*<')

    def test_current_tags_lists_the_selection_and_nothing_else(self):
        """The pill list and the checkboxes must not be able to disagree.

        They are one `selected` collection server-side, and the widget's
        script rebuilds the pills from the checkboxes, so "Remove all tags"
        cannot leave pills on screen beside "No tags are attached, yet."
        """
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                sheet = self.sheet(sheettype)
                chosen = self.vocabulary(sheettype)[:2]
                sheet.tags.set(chosen)

                html = self.edit_page(sheettype, sheet.pk)
                pills = current_tag_pills(html)

                self.assertEqual(pills, [tag.name for tag in chosen])
                self.assertIn('id="tag-selector-empty" hidden', html)

    def test_a_factsheet_with_no_tags_says_so_and_lists_no_pills(self):
        sheet = self.sheet("model")
        sheet.tags.clear()

        html = self.edit_page("model", sheet.pk)

        self.assertEqual(current_tag_pills(html), [])
        self.assertNotIn('id="tag-selector-empty" hidden', html)

    def test_the_dead_table_input_is_gone(self):
        """`tag_selector.html` was lifted from `dataedit`, which posts tags to
        its own endpoint with a `table`. Nothing in `modelview` ever passed
        one.
        """
        html = self.edit_page("model", self.sheet("model").pk)

        self.assertNotIn('name="table"', html)


class TestEveryWriteIsLogged(FactsheetWriteTestCase):
    """One logfmt line per write, matching the one the delete path emits."""

    def test_an_update_emits_one_structured_log_line(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                sheet = self.sheet(sheettype)
                chosen = [t.pk for t in self.vocabulary(sheettype)[:2]]

                with self.assertLogs("oeplatform", level="INFO") as logs:
                    self.submit(sheettype, sheet, tags=chosen)

                lines = [line for line in logs.output if "factsheet_write" in line]
                self.assertEqual(len(lines), 1)
                self.assertIn("sheettype=%s" % sheettype, lines[0])
                self.assertIn("action=update", lines[0])
                self.assertIn("pk=%s" % sheet.pk, lines[0])
                self.assertIn("tags=2", lines[0])
                self.assertIn("user=%s" % self.user.name, lines[0])

    def test_a_create_emits_one_structured_log_line(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                values = form_values(
                    sheettype, model_name="Created %s factsheet" % sheettype
                )
                data = as_post_data(values)
                data["tags"] = [t.pk for t in self.vocabulary(sheettype)[:1]]

                with self.assertLogs("oeplatform", level="INFO") as logs:
                    self.post(
                        "modelview:modeladd",
                        data=data,
                        kwargs={"sheettype": sheettype},
                        logged_in=True,
                    )

                lines = [line for line in logs.output if "factsheet_write" in line]
                self.assertEqual(len(lines), 1)
                self.assertIn("action=add", lines[0])
                self.assertIn("tags=1", lines[0])
