"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The tables tab's Publishable, Review, Datasets and Topics columns (#2554,
spec #2551), as seen through HTTP: what each row says, how the two new sorts
order the list, and what a screen reader is told about a cell with no text.

Assertions are on what the page says (rows, counts, links, labels), never on
markup details or seconds.
"""  # noqa: 501

from unittest import mock

from django.db.models import Q
from django.urls import reverse

from dataedit.models import Dataset, PeerReview, Table, Topic
from login.models import ADMIN_PERM, WRITE_PERM, UserPermission
from login.tests.test_tables_tab import TablesTabTestCase
from oeplatform.settings import PSEUDO_TOPIC_DRAFT

OPEN_LICENSE = {
    "metaMetadata": {"metadataVersion": "OEMetadata-2.0.4"},
    "resources": [
        {
            "licenses": [
                {
                    "name": "CC-BY-4.0",
                    "title": "Creative Commons Attribution 4.0 International",
                }
            ]
        }
    ],
}

NO_LICENSE = {
    "metaMetadata": {"metadataVersion": "OEMetadata-2.0.4"},
    "resources": [{}],
}


class ColumnTestCase(TablesTabTestCase):
    def row(self, name, query=None):
        return next(row for row in self.page(query).rows if row.table.name == name)


class PublishableColumnTests(ColumnTestCase):
    def test_an_open_license_passes_the_gate(self):
        self.table("t_open", oemetadata=OPEN_LICENSE)
        row = self.row("t_open")
        self.assertTrue(row.publishable)
        self.assertEqual(
            [(check.name, check.passed) for check in row.checks], [("License", True)]
        )

    def test_a_failing_license_names_the_check_and_gives_the_reason(self):
        self.table("t_unlicensed", oemetadata=NO_LICENSE)
        row = self.row("t_unlicensed")
        self.assertFalse(row.publishable)
        self.assertEqual(row.failed_label, "License")
        self.assertIn("No license information", row.checks[0].reason)

    def test_a_table_without_metadata_fails_with_a_reason(self):
        self.table("t_empty")
        row = self.row("t_empty")
        self.assertFalse(row.publishable)
        self.assertTrue(row.checks[0].reason)

    def test_published_tables_are_checked_too(self):
        """Metadata can be edited after publishing; the row must notice."""
        self.table("t_broken_after", published=True, oemetadata=NO_LICENSE)
        self.assertFalse(self.row("t_broken_after").publishable)

    def test_the_reasons_link_the_license_list_and_the_metadata_editor(self):
        self.table("t_fixme", oemetadata=NO_LICENSE)
        response = self.get()
        self.assertContains(response, "https://spdx.github.io/license-list-data/")
        self.assertContains(
            response, reverse("dataedit:meta_edit", kwargs={"table": "t_fixme"})
        )

    def test_the_gate_runs_for_the_visible_rows_only(self):
        tables = Table.objects.bulk_create(
            Table(name=f"t_{index:02d}") for index in range(30)
        )
        UserPermission.objects.bulk_create(
            UserPermission(holder=self.user, table=table, level=ADMIN_PERM)
            for table in tables
        )
        with mock.patch.object(
            Table,
            "validate_open_data_license",
            autospec=True,
            return_value={"status": True, "error": ""},
        ) as gate:
            self.get()
        self.assertEqual(gate.call_count, 25)

    def test_screen_readers_hear_the_result_and_what_a_click_does(self):
        self.table("t_ok", oemetadata=OPEN_LICENSE)
        self.table("t_bad", oemetadata=NO_LICENSE)
        response = self.get()
        self.assertContains(response, "Publishable. Show the publish checks")
        self.assertContains(response, "Not publishable:")


class ReviewColumnTests(ColumnTestCase):
    def review(self, table, finished=False, badge=None):
        return PeerReview.objects.create(
            table=table.name,
            contributor=self.user,
            reviewer=self.stranger,
            is_finished=finished,
            review={"badge": badge} if badge else {},
        )

    def test_no_review_reads_not_reviewed(self):
        self.table("t_plain")
        row = self.row("t_plain")
        self.assertEqual((row.review_state, row.review_id), ("not_reviewed", None))

    def test_an_unfinished_review_reads_in_review(self):
        table = self.table("t_open_review")
        self.review(table)
        row = self.row("t_open_review")
        self.assertEqual((row.review_state, row.review_id), ("in_review", None))

    def test_a_finished_review_reads_reviewed_with_its_badge_and_link(self):
        table = self.table("t_reviewed")
        review = self.review(table, finished=True, badge="Bronze")
        response = self.get()
        row = next(r for r in response.context["page"].rows)
        self.assertEqual(
            (row.review_state, row.review_badge, row.review_id),
            ("reviewed", "Bronze", review.pk),
        )
        self.assertContains(
            response,
            reverse(
                "dataedit:peer_review_reviewer",
                kwargs={"table": "t_reviewed", "review_id": review.pk},
            ),
        )
        self.assertContains(response, "Reviewed, badge Bronze. Open the review")

    def test_a_later_round_does_not_retract_a_finished_review(self):
        table = self.table("t_second_round")
        finished = self.review(table, finished=True, badge="Gold")
        self.review(table)
        row = self.row("t_second_round")
        self.assertEqual(
            (row.review_state, row.review_badge, row.review_id),
            ("reviewed", "Gold", finished.pk),
        )

    def test_the_badge_is_normalised(self):
        table = self.table("t_platin")
        self.review(table, finished=True, badge="platin")
        self.assertEqual(self.row("t_platin").review_badge, "Platinum")

    def test_a_finished_review_without_a_badge_still_reads_reviewed(self):
        table = self.table("t_no_badge")
        self.review(table, finished=True)
        row = self.row("t_no_badge")
        self.assertEqual((row.review_state, row.review_badge), ("reviewed", ""))

    def test_a_review_of_another_table_does_not_count(self):
        self.table("t_mine")
        other = Table.objects.create(name="t_someone_elses")
        self.review(other, finished=True, badge="Iron")
        self.assertEqual(self.row("t_mine").review_state, "not_reviewed")

    def test_sorted_not_reviewed_then_in_review_then_reviewed(self):
        reviewed = self.table("t_a", title="A")
        in_review = self.table("t_b", title="B")
        self.table("t_c", title="C")
        self.review(reviewed, finished=True, badge="Iron")
        self.review(in_review)
        self.assertEqual(self.names({"sort": "review"}), ["t_c", "t_b", "t_a"])
        self.assertEqual(self.names({"sort": "-review"}), ["t_a", "t_b", "t_c"])

    def test_the_review_header_sorts_and_says_so(self):
        self.table("t_any")
        link = self.page({"sort": "review"}).sort_links["review"]
        self.assertEqual(link.aria_sort, "ascending")
        self.assertEqual(link.url, f"{self.path}?sort=-review")


class DatasetsColumnTests(ColumnTestCase):
    def dataset(self, name, creator, *tables):
        dataset = Dataset.objects.create(name=name, creator=creator)
        dataset.tables.add(*tables)
        return dataset

    def test_a_table_in_no_dataset_says_so(self):
        self.table("t_alone")
        response = self.get()
        self.assertEqual(response.context["page"].rows[0].datasets, [])
        self.assertContains(response, "In no dataset")

    def test_own_datasets_first_then_other_peoples_named_with_their_owner(self):
        table = self.table("t_used")
        self.dataset("zz_mine", self.user, table)
        self.dataset("aa_theirs", self.stranger, table)
        self.dataset("mm_mine", self.user, table)
        datasets = self.row("t_used").datasets
        self.assertEqual(
            [(d.name, d.own, d.owner) for d in datasets],
            [
                ("mm_mine", True, ""),
                ("zz_mine", True, ""),
                ("aa_theirs", False, "TablesTabStranger"),
            ],
        )

    def test_a_dataset_without_creator_is_someone_elses(self):
        table = self.table("t_orphaned")
        self.dataset("ownerless", None, table)
        datasets = self.row("t_orphaned").datasets
        self.assertEqual(
            [(d.name, d.own, d.owner) for d in datasets], [("ownerless", False, "")]
        )

    def test_the_count_is_said_to_screen_readers(self):
        table = self.table("t_counted")
        self.dataset("one", self.user, table)
        self.dataset("two", self.stranger, table)
        self.assertContains(self.get(), "In 2 datasets. Show them")

    def test_a_strangers_draft_dataset_is_never_counted_or_named(self):
        """Dataset has no lifecycle yet, so no draft exists to make: the
        rule is proven by giving ``PUBLISHED_DATASETS`` the condition the
        lifecycle will, under which ``their_draft`` and ``my_draft`` are
        drafts. Mine still shows; theirs never does, in the cell or the
        sort."""
        counted = self.table("t_counted", title="A")
        uncounted = self.table("t_uncounted", title="B")
        self.dataset("their_draft", self.stranger, counted, uncounted)
        self.dataset("my_draft", self.user, counted)
        self.dataset("their_published", self.stranger, counted, uncounted)
        drafts = ~Q(name__in=["their_draft", "my_draft"])
        with mock.patch("login.tables_tab.PUBLISHED_DATASETS", drafts):
            page = self.page()
            descending = self.names({"sort": "-datasets"})
            body = self.get().content.decode()
        names = {row.table.name: [d.name for d in row.datasets] for row in page.rows}
        self.assertEqual(
            names,
            {
                "t_counted": ["my_draft", "their_published"],
                "t_uncounted": ["their_published"],
            },
        )
        self.assertEqual(descending, ["t_counted", "t_uncounted"])
        self.assertNotIn("their_draft", body)

    def test_today_every_strangers_dataset_is_published(self):
        """The characterisation the test above stands beside: until Dataset
        has a lifecycle, every Dataset is publicly listed, so it counts."""
        table = self.table("t_listed")
        self.dataset("anyones", self.stranger, table)
        self.assertEqual([d.name for d in self.row("t_listed").datasets], ["anyones"])

    def test_sorted_by_the_visible_count_then_title(self):
        one = self.table("t_one", title="One")
        two = self.table("t_two", title="Two")
        self.table("t_none", title="None")
        also_one = self.table("t_also_one", title="Also one")
        self.dataset("d1", self.user, one, two, also_one)
        self.dataset("d2", self.stranger, two)
        self.assertEqual(
            self.names({"sort": "datasets"}),
            ["t_none", "t_also_one", "t_one", "t_two"],
        )
        self.assertEqual(
            self.names({"sort": "-datasets"}),
            ["t_two", "t_also_one", "t_one", "t_none"],
        )

    def test_the_sort_does_not_multiply_the_rows_or_the_counts(self):
        table = self.table("t_busy")
        for index in range(3):
            self.dataset(f"d{index}", self.user, table)
        page = self.page({"sort": "-datasets"})
        self.assertEqual([row.table.name for row in page.rows], ["t_busy"])
        self.assertEqual(page.counts["all"], 1)


class TopicsColumnTests(ColumnTestCase):
    def topics(self, table, *names):
        for name in names:
            table.topics.add(Topic.objects.get_or_create(name=name)[0])

    def test_no_topics_says_so(self):
        self.table("t_untopical")
        response = self.get()
        self.assertEqual(response.context["page"].rows[0].topics, [])
        self.assertContains(response, "No topics")

    def test_two_chips_then_the_rest_behind_plus_n(self):
        table = self.table("t_topical")
        self.topics(table, "society", "energy", "model_draft")
        row = self.row("t_topical")
        self.assertEqual(row.shown_topics, ["energy", "model_draft"])
        self.assertEqual(row.more_topics, ["society"])
        self.assertContains(self.get(), "1 more topic. Show it")

    def test_two_topics_need_no_plus_n(self):
        table = self.table("t_two_topics")
        self.topics(table, "energy", "society")
        self.assertEqual(self.row("t_two_topics").more_topics, [])

    def test_the_draft_pseudo_topic_is_never_a_topic(self):
        table = self.table("t_drafty")
        self.topics(table, PSEUDO_TOPIC_DRAFT, "energy")
        self.assertEqual(self.row("t_drafty").topics, ["energy"])

    def test_an_unpublished_table_keeps_its_topics(self):
        table = self.table("t_was_published")
        self.topics(table, "energy")
        self.assertEqual(self.row("t_was_published").topics, ["energy"])


class AccessCellTests(ColumnTestCase):
    def test_the_access_cell_opens_the_access_drawer(self):
        self.table("t_shared", level=WRITE_PERM)
        response = self.get()
        self.assertContains(
            response,
            'hx-get="%s"'
            % reverse(
                "login:table-access",
                kwargs={"user_id": self.user.pk, "table_name": "t_shared"},
            ),
        )
        self.assertContains(
            response, "Access: You, your role Data editor. Manage access"
        )
