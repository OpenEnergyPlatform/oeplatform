"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The datasets tab's members drawer (#2625, spec #2613): every member of one of
the user's own Datasets, paged and searchable; an add search over the curation
rule (``assignable_tables``); Add and Remove acting at once through the
Dataset action service with ``via="dashboard"``; the hand-off to the tables
tab; and the drawer's openers on the list, as seen through HTTP.

Assertions are on what the user is offered and told, what the database holds
afterwards, which response headers came back, which log lines were written
and how many queries a read costs; never on markup details or seconds.
"""  # noqa: 501

import json
from datetime import timedelta

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from dataedit.models import Dataset, Embargo, Table, Topic
from login.dataset_members import PAGE_SIZE
from login.models import GroupPermission, Membership, Organization, UserPermission
from login.permissions import NO_PERM, WRITE_PERM
from login.tests.helpers import HTMX
from login.tests.test_dataset_actions import LONG_AGO, DatasetActionTestCase
from login.tests.test_profile_owner_rule import without_csrf
from modelview.tests.html import element_markup, element_with_id, text

DRAWER = "login/partials/dataset_members_drawer.html"


class MembersTestCase(DatasetActionTestCase):
    def members_path(self, name):
        return reverse("login:dataset-members", args=[self.user.pk, name])

    def search_path(self, name):
        return reverse("login:dataset-members-search", args=[self.user.pk, name])

    def drawer(self, name, query=None, status=200, **headers):
        response = self.client.get(
            self.members_path(name), query or {}, **HTMX, **headers
        )
        self.assertEqual(response.status_code, status)
        return response

    def mine(self, name, level=WRITE_PERM, **extra):
        """A Table the user holds ``level`` on, directly."""
        table = self.table(name, **extra)
        UserPermission.objects.create(holder=self.user, table=table, level=level)
        return table

    def write(self, name, data, **headers):
        """POST a change to ``name``'s members, its after-commit work run."""
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(self.members_path(name), data, **HTMX, **headers)

    def logged(self, name, data):
        with self.assertLogs("oeplatform.dataset_actions", "INFO") as logs:
            response = self.write(name, data)
        return response, logs.output

    def silent(self, name, data):
        with self.assertNoLogs("oeplatform.dataset_actions", "INFO"):
            return self.write(name, data)

    def member_names(self, response):
        return [row.table.name for row in response.context["members"].rows]

    def candidate_names(self, response):
        return [row.table.name for row in response.context["candidates"].rows]

    def modified(self, dataset):
        dataset.refresh_from_db()
        return dataset.modified_at


class DrawerReadTests(MembersTestCase):
    def test_lists_every_member_twenty_five_per_page_by_title(self):
        tables = [self.table(f"m_page_{n:02d}", title=f"T {n:02d}") for n in range(30)]
        self.dataset("ds_paged", tables=tables)
        first = self.drawer("ds_paged")
        self.assertTemplateUsed(first, DRAWER)
        self.assertEqual(len(self.member_names(first)), PAGE_SIZE)
        self.assertEqual(self.member_names(first)[0], "m_page_00")
        second = self.drawer("ds_paged", {"page": "2"})
        self.assertEqual(
            self.member_names(second), [f"m_page_{n:02d}" for n in range(25, 30)]
        )
        self.assertIn("In this dataset (30)", self.body(first, "dataset-members-count"))

    def test_search_over_members_matches_title_and_name(self):
        self.dataset(
            "ds_find",
            tables=[
                self.table("m_wind", title="Offshore turbines"),
                self.table("m_solar_wind", title="PV"),
                self.table("m_grid", title="Grid"),
            ],
        )
        response = self.drawer("ds_find", {"search": "WIND"})
        self.assertEqual(self.member_names(response), ["m_wind", "m_solar_wind"])
        response = self.drawer("ds_find", {"search": "turbine"})
        self.assertEqual(self.member_names(response), ["m_wind"])

    def test_members_carry_draft_and_embargoed_badges(self):
        draft = self.mine("m_badge_draft", published=False)
        embargoed = self.mine("m_badge_emb", embargoed=True)
        plain = self.table("m_badge_plain")
        self.dataset("ds_badges", tables=[draft, embargoed, plain])
        response = self.drawer("ds_badges")
        rows = {
            name: self.body(response, f"dataset-member-{table.pk}")
            for name, table in (("draft", draft), ("emb", embargoed), ("plain", plain))
        }
        self.assertIn("Draft", rows["draft"])
        self.assertIn("Embargoed", rows["emb"])
        self.assertNotIn("Draft", rows["plain"])
        self.assertNotIn("Embargoed", rows["plain"])

    def test_only_the_list_part_answers_a_search_inside_the_drawer(self):
        self.dataset("ds_part", tables=[self.table("m_part")])
        response = self.drawer("ds_part", HTTP_HX_TARGET="dataset-members-list")
        body = response.content.decode()
        self.assertIn('id="dataset-members-list"', body)
        self.assertNotIn('id="dataset-members-title"', body)

    def test_the_title_names_the_dataset_and_carries_its_key(self):
        self.dataset("ds_key", title="Heat atlas")
        response = self.drawer("ds_key")
        title = element_with_id(response.content.decode(), "dataset-members-title")
        self.assertIn('data-drawer-key="ds_key"', title)
        self.assertIn("Heat atlas", self.body(response, "dataset-members-title"))


class AddSearchTests(MembersTestCase):
    def setUp(self):
        super().setUp()
        self.own = self.mine("a_own_draft", title="Own draft", published=False)
        self.own_published = self.mine("a_own_pub", title="Own published")
        self.read_only = self.table("a_read_only", title="Read only")
        UserPermission.objects.create(
            holder=self.user, table=self.read_only, level=NO_PERM
        )
        self.theirs = self.table("a_their_pub", title="Their published wind")
        self.their_draft = self.table(
            "a_their_draft", title="Their draft wind", published=False
        )
        self.their_embargoed = self.table(
            "a_their_emb", title="Their embargoed wind", embargoed=True
        )
        self.dataset("ds_add")

    def search(self, query=None, **headers):
        response = self.client.get(
            self.search_path("ds_add"), query or {}, **HTMX, **headers
        )
        self.assertEqual(response.status_code, 200)
        return response

    def test_before_anything_is_typed_it_lists_the_users_own_tables(self):
        self.assertEqual(
            self.candidate_names(self.search()), ["a_own_draft", "a_own_pub"]
        )
        self.assertEqual(
            self.candidate_names(self.drawer("ds_add")), ["a_own_draft", "a_own_pub"]
        )

    def test_typed_it_searches_every_table_the_user_may_add(self):
        names = self.candidate_names(self.search({"add_search": "Wind"}))
        self.assertEqual(names, ["a_their_pub"])
        names = self.candidate_names(self.search({"add_search": "a_"}))
        self.assertEqual(
            names, ["a_own_draft", "a_own_pub", "a_read_only", "a_their_pub"]
        )

    def test_a_strangers_draft_or_embargoed_table_never_appears(self):
        for query in ("their", "a_their_draft", "a_their_emb", ""):
            with self.subTest(query=query):
                names = self.candidate_names(self.search({"add_search": query}))
                self.assertNotIn("a_their_draft", names)
                self.assertNotIn("a_their_emb", names)

    def test_paged_not_capped(self):
        for n in range(PAGE_SIZE + 5):
            self.table(f"a_many_{n:02d}")
        first = self.search({"add_search": "a_many"})
        self.assertEqual(len(self.candidate_names(first)), PAGE_SIZE)
        self.assertEqual(first.context["candidates"].total, PAGE_SIZE + 5)
        second = self.search({"add_search": "a_many", "add_page": "2"})
        self.assertEqual(len(self.candidate_names(second)), 5)

    def test_an_existing_member_reads_already_in(self):
        Dataset.objects.get(name="ds_add").tables.add(self.own_published)
        response = self.search()
        self.assertIn(
            "Already in",
            self.body(response, f"dataset-candidate-{self.own_published.pk}"),
        )
        self.assertNotIn(
            f'id="dataset-members-add-{self.own_published.pk}"',
            response.content.decode(),
        )
        self.assertIn(
            f'id="dataset-members-add-{self.own.pk}"', response.content.decode()
        )

    def test_only_the_results_part_answers(self):
        body = self.search().content.decode()
        self.assertIn('id="dataset-members-results"', body)
        self.assertNotIn('id="dataset-members-title"', body)


class AddTests(MembersTestCase):
    def test_adding_a_strangers_published_table_works_and_stays_in_the_drawer(self):
        dataset = self.dataset("ds_add_one", modified=LONG_AGO)
        theirs = self.table("w_their_pub", title="Their table")
        response, logs = self.logged(
            "ds_add_one", {"op": "add", "table": "w_their_pub", "add_search": "their"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, DRAWER)
        self.assertEqual(list(dataset.tables.all()), [theirs])
        self.assertGreater(self.modified(dataset), LONG_AGO)
        changed = json.loads(response["HX-Trigger"])["datasets-changed"]
        self.assertTrue(changed["stay"])
        self.assertEqual(len(logs), 1)
        self.assertIn(
            "dataset=ds_add_one action=members_add table=w_their_pub", logs[0]
        )
        self.assertIn("via=dashboard", logs[0])
        # the add search is still what it was, and the row reads "Added"
        self.assertEqual(response.context["candidates"].search, "their")
        self.assertIn("Added", self.body(response, f"dataset-members-add-{theirs.pk}"))
        self.assertIn("Added", self.body(response, "dataset-members-message"))

    def test_seeded_topics_are_named(self):
        self.dataset("ds_seed", topics=["energy"])
        table = self.table("w_seed")
        for name in ("scenario", "energy"):
            table.topics.add(Topic.objects.get_or_create(name=name)[0])
        response, _ = self.logged("ds_seed", {"op": "add", "table": "w_seed"})
        self.assertIn(
            "Its topic scenario was added to the dataset.",
            self.body(response, "dataset-members-message"),
        )

    def test_several_seeded_topics_are_named_in_the_plural(self):
        self.dataset("ds_seeds")
        table = self.table("w_seeds")
        for name in ("scenario", "grid"):
            table.topics.add(Topic.objects.get_or_create(name=name)[0])
        response, _ = self.logged("ds_seeds", {"op": "add", "table": "w_seeds"})
        self.assertIn(
            "Its topics grid, scenario were added to the dataset.",
            self.body(response, "dataset-members-message"),
        )

    def test_an_already_member_is_a_no_op(self):
        table = self.table("w_again")
        dataset = self.dataset("ds_again", tables=[table], modified=LONG_AGO)
        response = self.silent("ds_again", {"op": "add", "table": "w_again"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("HX-Trigger", response)
        self.assertEqual(self.modified(dataset), LONG_AGO)
        self.assertIn("already in", self.body(response, "dataset-members-message"))

    def test_a_strangers_draft_is_refused_and_nothing_is_written(self):
        dataset = self.dataset("ds_refuse", modified=LONG_AGO)
        self.table("w_their_draft", published=False)
        response = self.silent("ds_refuse", {"op": "add", "table": "w_their_draft"})
        self.assertEqual(response.status_code, 409)
        self.assertTemplateUsed(response, DRAWER)
        self.assertEqual(dataset.tables.count(), 0)
        self.assertEqual(self.modified(dataset), LONG_AGO)
        self.assertIn(
            "Nothing was changed", self.body(response, "dataset-members-message")
        )

    def test_naming_no_table_is_an_unusable_request(self):
        self.dataset("ds_nothing")
        response = self.silent("ds_nothing", {"op": "add", "table": ""})
        self.assertEqual(response.status_code, 400)
        response = self.silent("ds_nothing", {"op": "rename", "table": "x"})
        self.assertEqual(response.status_code, 400)


class RemoveTests(MembersTestCase):
    def test_remove_acts_at_once_whoever_holds_the_member(self):
        theirs = self.table("r_theirs")
        kept = self.table("r_kept")
        dataset = self.dataset(
            "ds_remove", tables=[theirs, kept], topics=["energy"], modified=LONG_AGO
        )
        response, logs = self.logged("ds_remove", {"op": "remove", "table": "r_theirs"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(dataset.tables.all()), [kept])
        self.assertEqual(
            list(dataset.topics.values_list("name", flat=True)), ["energy"]
        )
        self.assertGreater(self.modified(dataset), LONG_AGO)
        self.assertTrue(json.loads(response["HX-Trigger"])["datasets-changed"]["stay"])
        self.assertEqual(len(logs), 1)
        self.assertIn("dataset=ds_remove action=members_remove table=r_theirs", logs[0])

    def test_remove_is_a_neutral_button(self):
        table = self.table("r_neutral")
        self.dataset("ds_neutral", tables=[table])
        button = element_with_id(
            self.drawer("ds_neutral").content.decode(),
            f"dataset-members-remove-{table.pk}",
        )
        self.assertIn("btn-outline-secondary", button)
        self.assertNotIn("danger", button)
        self.assertIn("hx-post", button)

    def test_a_member_the_user_could_not_add_back_asks_first(self):
        theirs = self.table("r_their_draft", title="Their draft", published=False)
        dataset = self.dataset("ds_ask", tables=[theirs], modified=LONG_AGO)
        drawer = self.drawer("ds_ask").content.decode()
        # the page read already knows: its Remove asks instead of posting
        button = element_with_id(drawer, f"dataset-members-remove-{theirs.pk}")
        self.assertNotIn("hx-post", button)
        self.assertIn("ask=r_their_draft", button)
        asked = self.drawer("ds_ask", {"ask": "r_their_draft"})
        self.assertIn(
            "You will not be able to add it back while it is a draft.",
            self.body(asked, "dataset-members-confirm-box"),
        )
        # a POST without the confirmation asks too, and writes nothing
        response = self.silent("ds_ask", {"op": "remove", "table": "r_their_draft"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("HX-Trigger", response)
        self.assertIn("add it back", self.body(response, "dataset-members-confirm-box"))
        self.assertEqual(list(dataset.tables.all()), [theirs])
        self.assertEqual(self.modified(dataset), LONG_AGO)
        response, logs = self.logged(
            "ds_ask", {"op": "remove", "table": "r_their_draft", "confirm": "yes"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(dataset.tables.count(), 0)
        self.assertEqual(len(logs), 1)

    def test_an_embargoed_member_says_embargoed(self):
        theirs = self.table("r_their_emb", embargoed=True)
        self.dataset("ds_ask_emb", tables=[theirs])
        asked = self.drawer("ds_ask_emb", {"ask": "r_their_emb"})
        self.assertIn(
            "You will not be able to add it back while it is embargoed.",
            self.body(asked, "dataset-members-confirm-box"),
        )

    def test_a_draft_the_user_holds_data_editor_on_is_removed_at_once(self):
        own_draft = self.mine("r_own_draft", published=False)
        dataset = self.dataset("ds_own_draft", tables=[own_draft])
        button = element_with_id(
            self.drawer("ds_own_draft").content.decode(),
            f"dataset-members-remove-{own_draft.pk}",
        )
        self.assertIn("hx-post", button)
        self.logged("ds_own_draft", {"op": "remove", "table": "r_own_draft"})
        self.assertEqual(dataset.tables.count(), 0)

    def test_removing_the_last_member_of_a_published_dataset_keeps_it_published(self):
        dataset = self.ready("ds_last", published=timezone.now())
        response, _ = self.logged("ds_last", {"op": "remove", "table": "ds_last_t"})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(self.published_at(dataset))
        self.assertIn("stays published", self.body(response, "dataset-members-message"))

    def test_removing_a_non_member_is_a_no_op(self):
        self.table("r_stranger")
        dataset = self.dataset("ds_not_in", modified=LONG_AGO)
        response = self.silent("ds_not_in", {"op": "remove", "table": "r_stranger"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("HX-Trigger", response)
        self.assertEqual(self.modified(dataset), LONG_AGO)


class HandOffTests(MembersTestCase):
    def test_counts_the_members_the_user_holds_data_editor_or_more_on(self):
        direct = self.mine("h_direct")
        read_only = self.table("h_read_only")
        UserPermission.objects.create(holder=self.user, table=read_only, level=NO_PERM)
        through_org = self.table("h_org")
        organization = Organization.objects.create(name="h_org_org")
        Membership.objects.create(user=self.user, group=organization)
        GroupPermission.objects.create(
            holder=organization, table=through_org, level=WRITE_PERM
        )
        theirs = self.table("h_theirs")
        self.dataset("ds_handoff", tables=[direct, read_only, through_org, theirs])
        response = self.drawer("ds_handoff")
        handoff = element_markup(response.content.decode(), "dataset-members-handoff")
        self.assertIn(
            f'{reverse("login:tables", args=[self.user.pk])}?dataset=ds_handoff',
            handoff,
        )
        self.assertIn("2 of its tables are yours", text(handoff))

    def test_hidden_when_no_member_is_the_users(self):
        self.dataset("ds_no_handoff", tables=[self.table("h_only_theirs")])
        body = self.drawer("ds_no_handoff").content.decode()
        self.assertNotIn('id="dataset-members-handoff"', body)


class GateLineTests(MembersTestCase):
    def test_an_empty_draft_says_what_publishing_needs(self):
        self.dataset("ds_gate")
        gate = self.body(self.drawer("ds_gate"), "dataset-members-gate")
        self.assertIn("add at least one table", gate)
        self.assertIn(
            "choose at least one topic (Edit…, or add a table that has one)", gate
        )

    def test_a_draft_passing_the_gate_and_a_published_dataset_say_nothing(self):
        self.ready("ds_gate_ready")
        self.ready("ds_gate_pub", published=timezone.now())
        for name in ("ds_gate_ready", "ds_gate_pub"):
            with self.subTest(name=name):
                body = self.drawer(name).content.decode()
                self.assertNotIn('id="dataset-members-gate"', body)


class NotTheUsersDatasetTests(MembersTestCase):
    def test_a_foreign_or_unknown_dataset_is_404_on_every_drawer_route(self):
        self.dataset("ds_their_draft_404", creator=self.stranger)
        self.dataset(
            "ds_their_pub_404", creator=self.stranger, published=timezone.now()
        )
        table = self.table("n_table")
        for name in ("ds_their_draft_404", "ds_their_pub_404", "ds_nobody_has_it"):
            with self.subTest(name=name):
                self.assertEqual(
                    self.client.get(self.members_path(name), **HTMX).status_code, 404
                )
                self.assertEqual(
                    self.client.get(self.search_path(name), **HTMX).status_code, 404
                )
                response = self.silent(name, {"op": "add", "table": table.name})
                self.assertEqual(response.status_code, 404)
        self.assertEqual(table.datasets.count(), 0)

    def test_a_foreign_draft_reads_exactly_like_an_unknown_name(self):
        self.dataset("ds_their_secret", creator=self.stranger)
        foreign = self.client.get(self.members_path("ds_their_secret"))
        unknown = self.client.get(self.members_path("ds_no_secret"))
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(
            without_csrf(foreign).replace("ds_their_secret", "NAME"),
            without_csrf(unknown).replace("ds_no_secret", "NAME"),
        )


class DrawerQueryCountTests(MembersTestCase):
    """A drawer page costs the same at 25 and at 2,500 members: the members
    page, its count, the "can't add back" read (one query for the page,
    whatever it holds), the add search's page and count, the hand-off count
    and the publish gate's two checks."""

    def fill(self, name, members):
        tables = Table.objects.bulk_create(
            Table(name=f"{name}_{n:04d}", is_publish=n % 3 != 0) for n in range(members)
        )
        Embargo.objects.create(table=tables[1], duration="1_year")
        for table in tables[:3]:
            UserPermission.objects.create(
                holder=self.user, table=table, level=WRITE_PERM
            )
        dataset = self.dataset(name)
        through = Dataset.tables.through
        through.objects.bulk_create(
            through(dataset_id=dataset.pk, table_id=table.pk) for table in tables
        )
        return dataset

    def queries(self, name, query=None, path=None):
        path = path or self.members_path(name)
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(path, query or {}, **HTMX)
        self.assertEqual(response.status_code, 200)
        return len(context.captured_queries)

    def test_constant_at_25_and_2500_members(self):
        self.client.get(self.path, **HTMX)  # the current Site, cached per process
        self.fill("q_small", PAGE_SIZE)
        self.fill("q_large", 2500)
        small = self.queries("q_small")
        large = self.queries("q_large")
        self.assertEqual(small, large)
        self.assertEqual(large, 11)
        self.assertEqual(self.queries("q_large", {"search": "q_large_1"}), 12)
        self.assertEqual(
            self.queries("q_large", path=self.search_path("q_large")),
            self.queries("q_small", path=self.search_path("q_small")),
        )


class OpenersTests(MembersTestCase):
    def test_the_menu_offers_manage_tables(self):
        dataset = self.dataset("ds_menu_members")
        row = element_markup(self.get().content.decode(), f"row-{dataset.pk}")
        entry = element_markup(row, f"menu-{dataset.pk}-members")
        self.assertIn("Manage tables…", text(entry))
        self.assertIn(f'hx-get="{self.members_path("ds_menu_members")}"', entry)
        self.assertIn('hx-target="#dataset-members-body"', entry)
        self.assertIn(f'data-members-origin="menu-{dataset.pk}"', entry)
        self.assertLess(row.index("Manage tables…"), row.index("Publish…"))

    def test_and_n_more_opens_the_drawer(self):
        tables = [self.table(f"o_more_{n:02d}") for n in range(12)]
        dataset = self.dataset("ds_more", tables=tables)
        more = element_markup(self.get().content.decode(), f"mb-{dataset.pk}-more")
        self.assertEqual(text(more), "and 2 more")
        self.assertIn(f'hx-get="{self.members_path("ds_more")}"', more)
        self.assertIn(f'data-members-origin="mb-{dataset.pk}"', more)

    def test_the_publish_gate_dialog_links_to_manage_tables(self):
        dataset = self.dataset("ds_gate_link", topics=["energy"])
        dialog = self.preflight("publish", "ds_gate_link").content.decode()
        link = element_markup(dialog, "dataset-action-gate-members")
        self.assertIn("Manage tables…", text(link))
        self.assertIn("data-close-then", link)
        self.assertIn('hx-trigger="dialog-closed"', link)
        self.assertIn(f'hx-get="{self.members_path("ds_gate_link")}"', link)
        self.assertIn(f'data-members-origin="menu-{dataset.pk}"', link)

    def test_the_link_is_offered_when_only_a_topic_is_missing(self):
        # a member brings its Topics along, so adding one may be the fix
        self.dataset("ds_gate_topic", tables=[self.table("o_gate_t")])
        dialog = self.preflight("publish", "ds_gate_topic").content.decode()
        self.assertIn('id="dataset-action-gate-members"', dialog)

    def test_no_link_for_a_dataset_that_passes(self):
        self.ready("ds_gate_passes")
        dialog = self.preflight("publish", "ds_gate_passes").content.decode()
        self.assertNotIn('id="dataset-action-gate-members"', dialog)


class MembersInTheAddressTests(MembersTestCase):
    """``?members=<name>`` is page state: the page says whether it names one
    of the user's Datasets, and no list address ever carries it."""

    def drawer_element(self, response):
        return element_with_id(response.content.decode(), "dataset-members")

    def test_the_page_reopens_the_drawer_on_one_of_the_users_datasets(self):
        dataset = self.dataset("ds_open")
        element = self.drawer_element(self.get({"members": "ds_open"}))
        self.assertIn('data-open="ds_open"', element)
        self.assertIn(f'data-open-origin="menu-{dataset.pk}"', element)
        self.assertIn(f'data-url-template="{self.members_path("__key__")}"', element)

    def test_a_foreign_or_unknown_name_is_ignored(self):
        self.dataset("ds_their_open", creator=self.stranger, published=timezone.now())
        for name in ("ds_their_open", "ds_nobody", ""):
            with self.subTest(name=name):
                element = self.drawer_element(self.get({"members": name}))
                self.assertNotIn("data-open=", element)

    def test_no_list_address_carries_it(self):
        for n in range(30):
            self.dataset(f"ds_addr_{n:02d}")
        response = self.get({"members": "ds_addr_01", "sort": "dataset"})
        page = response.context["page"]
        self.assertNotIn("members", page.url)
        region = element_markup(response.content.decode(), "datasets-results")
        self.assertIn("page=2", region)
        self.assertNotIn("members=", region)
        pushed = self.get({"members": "ds_addr_01", "page": "2"}, htmx=True)
        self.assertNotIn("members", pushed["HX-Push-Url"])

    def test_the_htmx_region_does_not_look_it_up(self):
        self.dataset("ds_region_only")
        with CaptureQueriesContext(connection) as plain:
            self.get(htmx=True)
        with CaptureQueriesContext(connection) as named:
            self.get({"members": "ds_region_only"}, htmx=True)
        self.assertEqual(len(plain.captured_queries), len(named.captured_queries))


class LifecycleTests(MembersTestCase):
    def test_modified_moves_only_on_a_real_change(self):
        table = self.table("l_table")
        dataset = self.dataset("ds_life", modified=LONG_AGO)
        self.logged("ds_life", {"op": "add", "table": "l_table"})
        first = self.modified(dataset)
        self.assertGreater(first, LONG_AGO)
        Dataset.objects.filter(pk=dataset.pk).update(modified_at=LONG_AGO)
        self.silent("ds_life", {"op": "add", "table": "l_table"})
        self.assertEqual(self.modified(dataset), LONG_AGO)
        self.logged("ds_life", {"op": "remove", "table": table.name})
        self.assertGreater(self.modified(dataset), LONG_AGO)
        self.assertLess(LONG_AGO, timezone.now() - timedelta(days=1))
