"""A citation, resolved: is the data still there, and has anybody reviewed it.

The rule under test is **never block, never collect, resolve on read**. A
bundle is a published research record, so a link to a table that has since been
deleted is neither removed nor allowed to keep the table alive -- the read
simply says what the citation means now.

What that buys, and what each of these tests is really pinning:

- **Nothing can go stale**, because nothing is stored. The same link reads
  `false` and then `true` when its target appears, with no write to the bundle
  in between and no change to its version.
- **A catalogue reference is a live one.** `ref: table` is the reproducible
  citation, `ref: dataset` the current one, and the read resolves the second to
  the members the catalogue entry has today.
- **The review indicator is three-valued.** Absent is `null`, not `false`: the
  Open Peer Review process postdates most of the platform's data, and a boolean
  would present all of it as having failed review.
- **The cost is bounded by target kinds, not by citations.** A scenario with
  ten links costs a read exactly what a scenario with two costs it.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.db import connection
from django.test.utils import CaptureQueriesContext

from dataedit.models import Dataset, PeerReview, Table
from login.models import myuser
from oekg.resolution import REVIEW_FINISHED, REVIEW_IN_PROGRESS
from oekg.serializers import READ_ONLY_CONTAINER
from oekg.tests.bundle_fixtures import VALID_PAYLOAD
from oekg.tests.test_dataset_link_api import (
    DATASET_LINK,
    TABLE_LINK,
    DatasetLinkTestCase,
    ExternalLinkMixin,
)


class ResolutionTestCase(DatasetLinkTestCase):
    def meta_of(self, uid, sid, did):
        return self.client.get(self.link_url(uid, sid, did)).data[READ_ONLY_CONTAINER]

    def reviewers(self):
        """Two accounts, because a review may not be its own contributor.

        Made once per test and reused: a second review in the same test is a
        second round on the same table, not a second pair of people.
        """
        if not hasattr(self, "_reviewers"):
            self._reviewers = (
                myuser.objects.create_user(
                    name="reviewer", email="reviewer@example.org", affiliation=""
                ),
                myuser.objects.create_user(
                    name="contributor", email="contributor@example.org", affiliation=""
                ),
            )
        return self._reviewers


class TableReferenceResolutionTest(ResolutionTestCase):
    def test_a_link_to_an_existing_table_resolves(self):
        Table.objects.create(name="abbb_emob")

        uid, sid, did, _ = self.with_one_link()

        self.assertIs(self.meta_of(uid, sid, did)["resolvable"], True)

    def test_a_link_to_a_table_that_was_never_there_does_not_resolve(self):
        uid, sid, did, _ = self.with_one_link()

        self.assertIs(self.meta_of(uid, sid, did)["resolvable"], False)

    def test_a_deleted_target_reads_as_unresolvable_and_the_link_stays(self):
        # The whole decision in one test: the statement "this scenario used
        # that table" outlives the table, and the reader is told.
        Table.objects.create(name="abbb_emob")
        uid, sid, did, _ = self.with_one_link()

        Table.objects.filter(name="abbb_emob").delete()

        read = self.client.get(self.link_url(uid, sid, did))
        self.assertEqual(read.status_code, 200)
        self.assertEqual(read.data["name"], "abbb_emob")
        self.assertIs(read.data[READ_ONLY_CONTAINER]["resolvable"], False)

    def test_a_resolving_link_names_the_table_it_resolves_to(self):
        Table.objects.create(name="abbb_emob")

        uid, sid, did, _ = self.with_one_link()

        self.assertEqual(
            self.meta_of(uid, sid, did)["tables"],
            [{"name": "abbb_emob", "peer_review": None}],
        )

    def test_a_dead_link_resolves_to_no_tables(self):
        uid, sid, did, _ = self.with_one_link()

        self.assertEqual(self.meta_of(uid, sid, did)["tables"], [])

    def test_nothing_is_stored_so_nothing_goes_stale(self):
        # Computed per read: the link was written when its target did not
        # exist, and it starts resolving the moment the target does -- with no
        # write to the bundle, and so no change to its version.
        uid, sid, did, etag = self.with_one_link()
        self.assertIs(self.meta_of(uid, sid, did)["resolvable"], False)

        Table.objects.create(name="abbb_emob")

        response = self.client.get(self.link_url(uid, sid, did))
        self.assertIs(response.data[READ_ONLY_CONTAINER]["resolvable"], True)
        self.assertEqual(response["ETag"], etag)

    def test_the_collection_resolves_every_link_it_lists(self):
        Table.objects.create(name="abbb_emob")
        uid, sid, _, etag = self.with_one_link()
        self.add_link(uid, sid, etag, DATASET_LINK)

        listed = self.client.get(self.links_url(uid, sid)).data["results"]

        self.assertEqual(
            [row[READ_ONLY_CONTAINER]["resolvable"] for row in listed], [True, False]
        )

    def test_the_create_response_already_carries_the_resolution(self):
        Table.objects.create(name="abbb_emob")
        uid, sid, etag = self.with_one_scenario()

        response = self.add_link(uid, sid, etag)

        self.assertIs(response.data[READ_ONLY_CONTAINER]["resolvable"], True)


class DatasetReferenceResolutionTest(ResolutionTestCase):
    """`ref: dataset` is the *current* reference, and the read says what it means
    today rather than what it meant when the bundle was written."""

    def a_dataset_with(self, *table_names):
        dataset = Dataset.objects.create(name="my_dataset")
        for name in table_names:
            dataset.tables.add(Table.objects.create(name=name))
        return dataset

    def test_a_link_to_an_existing_catalogue_entry_resolves(self):
        self.a_dataset_with("t_one")

        uid, sid, did, _ = self.with_one_link(DATASET_LINK)

        self.assertIs(self.meta_of(uid, sid, did)["resolvable"], True)

    def test_it_resolves_to_the_entrys_current_members(self):
        self.a_dataset_with("t_one", "t_two")

        uid, sid, did, _ = self.with_one_link(DATASET_LINK)

        self.assertEqual(
            [row["name"] for row in self.meta_of(uid, sid, did)["tables"]],
            ["t_one", "t_two"],
        )

    def test_a_membership_change_shows_up_in_the_next_read(self):
        # The trade-off, made visible: a table reference is reproducible, a
        # catalogue reference is current. Freezing a snapshot would need a new
        # predicate on a closed shape.
        dataset = self.a_dataset_with("t_one")
        uid, sid, did, _ = self.with_one_link(DATASET_LINK)

        dataset.tables.add(Table.objects.create(name="t_two"))

        self.assertEqual(
            [row["name"] for row in self.meta_of(uid, sid, did)["tables"]],
            ["t_one", "t_two"],
        )

    def test_a_table_leaving_the_entry_shows_up_too(self):
        dataset = self.a_dataset_with("t_one", "t_two")
        uid, sid, did, _ = self.with_one_link(DATASET_LINK)

        dataset.tables.remove(Table.objects.get(name="t_two"))

        self.assertEqual(
            [row["name"] for row in self.meta_of(uid, sid, did)["tables"]], ["t_one"]
        )

    def test_an_entry_with_no_members_still_resolves(self):
        # Told apart from a deleted one: the entry is there, it just groups
        # nothing today.
        self.a_dataset_with()

        uid, sid, did, _ = self.with_one_link(DATASET_LINK)

        meta = self.meta_of(uid, sid, did)
        self.assertIs(meta["resolvable"], True)
        self.assertEqual(meta["tables"], [])

    def test_a_link_to_a_catalogue_entry_that_is_gone_does_not_resolve(self):
        self.a_dataset_with("t_one")
        uid, sid, did, _ = self.with_one_link(DATASET_LINK)

        Dataset.objects.filter(name="my_dataset").delete()

        meta = self.meta_of(uid, sid, did)
        self.assertIs(meta["resolvable"], False)
        self.assertEqual(meta["tables"], [])

    def test_an_ownerless_entry_still_resolves(self):
        # Resolving is not endorsing: Dataset.creator is nulled when its owner
        # is deleted, so a live target can be one nobody maintains.
        dataset = self.a_dataset_with("t_one")
        dataset.creator = None
        dataset.save()

        uid, sid, did, _ = self.with_one_link(DATASET_LINK)

        self.assertIs(self.meta_of(uid, sid, did)["resolvable"], True)


class PeerReviewIndicatorTest(ResolutionTestCase):
    """Three-valued on purpose: absent is not failed."""

    def review(self, table, is_finished):
        reviewer, contributor = self.reviewers()
        return PeerReview.objects.create(
            table=table,
            is_finished=is_finished,
            reviewer=reviewer,
            contributor=contributor,
        )

    def test_a_table_with_no_review_reports_none(self):
        Table.objects.create(name="abbb_emob")

        uid, sid, did, _ = self.with_one_link()

        self.assertIsNone(self.meta_of(uid, sid, did)["tables"][0]["peer_review"])

    def test_an_unfinished_review_reports_in_progress(self):
        Table.objects.create(name="abbb_emob")
        self.review("abbb_emob", is_finished=False)

        uid, sid, did, _ = self.with_one_link()

        self.assertEqual(
            self.meta_of(uid, sid, did)["tables"][0]["peer_review"],
            REVIEW_IN_PROGRESS,
        )

    def test_a_finished_review_reports_finished(self):
        Table.objects.create(name="abbb_emob")
        self.review("abbb_emob", is_finished=True)

        uid, sid, did, _ = self.with_one_link()

        self.assertEqual(
            self.meta_of(uid, sid, did)["tables"][0]["peer_review"], REVIEW_FINISHED
        )

    def test_a_later_round_does_not_undo_a_finished_one(self):
        # Having been through review is a fact a new round does not retract.
        Table.objects.create(name="abbb_emob")
        self.review("abbb_emob", is_finished=True)
        self.review("abbb_emob", is_finished=False)

        uid, sid, did, _ = self.with_one_link()

        self.assertEqual(
            self.meta_of(uid, sid, did)["tables"][0]["peer_review"], REVIEW_FINISHED
        )

    def test_a_review_outliving_its_table_reports_nothing(self):
        # PeerReview.table is a name, not a foreign key, so reviews survive
        # their tables. A review is reported for a table that resolves, and a
        # table that is gone resolves to nothing at all.
        Table.objects.create(name="abbb_emob")
        self.review("abbb_emob", is_finished=True)
        uid, sid, did, _ = self.with_one_link()

        Table.objects.filter(name="abbb_emob").delete()

        meta = self.meta_of(uid, sid, did)
        self.assertIs(meta["resolvable"], False)
        self.assertEqual(meta["tables"], [])

    def test_a_catalogue_entrys_members_carry_their_own_review_state(self):
        # The review process is per table, so there is no such thing as a
        # reviewed catalogue entry -- each member answers for itself.
        dataset = Dataset.objects.create(name="my_dataset")
        for name in ("t_one", "t_two"):
            dataset.tables.add(Table.objects.create(name=name))
        self.review("t_two", is_finished=True)

        uid, sid, did, _ = self.with_one_link(DATASET_LINK)

        self.assertEqual(
            self.meta_of(uid, sid, did)["tables"],
            [
                {"name": "t_one", "peer_review": None},
                {"name": "t_two", "peer_review": REVIEW_FINISHED},
            ],
        )


class ResolutionCostTest(ResolutionTestCase):
    """The read costs the same whatever a scenario cites."""

    def with_links(self, count, tag):
        """A scenario citing ``count`` tables and ``count`` catalogue entries.

        ``tag`` keeps two scenarios in one test from claiming the same acronym
        and the same table names -- the point is to compare two sizes, not to
        share fixtures between them.
        """
        uid, etag = self.created({**VALID_PAYLOAD, "acronym": f"COST-{tag}"})
        response = self.add_scenario(uid, etag)
        sid, etag = response.data[READ_ONLY_CONTAINER]["uid"], response["ETag"]
        for index in range(count):
            Table.objects.create(name=f"t{tag}_{index}")
            dataset = Dataset.objects.create(name=f"d{tag}_{index}")
            dataset.tables.add(Table.objects.create(name=f"m{tag}_{index}"))
            etag = self.add_link(
                uid, sid, etag, {**TABLE_LINK, "name": f"t{tag}_{index}"}
            )["ETag"]
            etag = self.add_link(
                uid, sid, etag, {**DATASET_LINK, "name": f"d{tag}_{index}"}
            )["ETag"]
        return uid, sid

    def queries_for(self, count, tag):
        uid, sid = self.with_links(count, tag)
        self.client.logout()
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(self.links_url(uid, sid))
        self.assertEqual(response.data["count"], count * 2)
        return len(captured)

    def test_ten_links_cost_a_read_what_two_cost_it(self):
        """Three queries either way: the tables, the catalogue entries with
        their members, and the reviews of everything those turned up.

        Pinned as an absolute rather than only as an equality, because two
        equal numbers would also be the answer if resolution silently stopped
        happening. Batched by target kind is the whole design: the per-link
        alternative would put a query per citation on a public endpoint.
        """
        self.assertEqual(
            [self.queries_for(5, "many"), self.queries_for(1, "few")], [3, 3]
        )


class UnroutableLinkResolutionTest(ExternalLinkMixin, ResolutionTestCase):
    """A link pointing somewhere this platform has no route for.

    The live graph holds databus URLs. `ref` already reads back null there,
    because the writable payload cannot express such an address -- and
    resolution says the same thing the same way. Answering `false` would claim
    the target had been deleted, which is a fabrication, not an answer.
    """

    def test_resolvability_reads_back_as_null_rather_than_false(self):
        uid, sid = self.with_an_external_link()

        read = self.client.get(self.link_url(uid, sid, "legacy")).data

        self.assertIsNone(read[READ_ONLY_CONTAINER]["resolvable"])

    def test_it_resolves_to_no_table_list_at_all(self):
        uid, sid = self.with_an_external_link()

        read = self.client.get(self.link_url(uid, sid, "legacy")).data

        self.assertIsNone(read[READ_ONLY_CONTAINER]["tables"])
