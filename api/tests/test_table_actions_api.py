"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The single-table API endpoints for publish, unpublish and delete go through
the table action service (#2569, spec #2551), the path the dashboard takes:
same request and response shapes as before (``{}`` / ``{"reason": ...}``),
but a publish is atomic, ``draft`` is refused as a Topic, and every action
logs ``via=api``.
"""  # noqa: 501

from copy import deepcopy
from unittest import mock

from django.db import connection
from oemetadata.v2.v20.example import OEMETADATA_V20_EXAMPLE

from api.services import table_actions
from dataedit.models import Embargo, Table, Topic
from oeplatform.settings import PSEUDO_TOPIC_DRAFT, TOPIC_SCENARIO

from . import APITestCaseWithTable

LOGGER = "oeplatform.table_actions"


class ActionAPITestCase(APITestCaseWithTable):
    test_table = "test_table_api_actions"

    def table(self):
        return Table.objects.filter(name=self.test_table).first()

    def make_publishable(self):
        self.api_req("post", path="meta/", data=deepcopy(OEMETADATA_V20_EXAMPLE))

    def publish(self, topic=TOPIC_SCENARIO, duration=None, **kwargs):
        data = {"embargo": {"duration": duration}} if duration else None
        return self.api_req("post", path=f"move_publish/{topic}/", data=data, **kwargs)


class PublishThroughTheServiceTests(ActionAPITestCase):
    def test_publishing_answers_an_empty_body_and_logs_via_api(self):
        self.make_publishable()
        # publish and unpublish log once the transaction has committed
        with self.assertLogs(LOGGER) as logs, self.captureOnCommitCallbacks(
            execute=True
        ):
            self.publish(duration="6_months", exp_res={})
        self.assertTrue(self.table().is_publish)
        self.assertEqual(
            list(self.table().topics.values_list("name", flat=True)), [TOPIC_SCENARIO]
        )
        (line,) = logs.output
        self.assertIn(f"table={self.test_table} action=publish", line)
        self.assertIn("via=api batch=-", line)
        self.assertIn(f"topic={TOPIC_SCENARIO} embargo=6_months", line)

    def test_an_unknown_topic_writes_nothing(self):
        """The old path set the embargo and moved the peer reviews before it
        looked the Topic up, then failed: a half-publish."""
        self.make_publishable()
        response = self.publish(topic="no_such_topic", duration="1_year", exp_code=400)
        self.assertIn("no_such_topic", response["reason"])
        self.assertFalse(self.table().is_publish)
        self.assertFalse(Embargo.objects.filter(table=self.table()).exists())

    def test_the_draft_pseudo_topic_is_refused(self):
        Topic.objects.get_or_create(name=PSEUDO_TOPIC_DRAFT)
        self.make_publishable()
        response = self.publish(topic=PSEUDO_TOPIC_DRAFT, exp_code=400)
        self.assertIn("Draft is a status", response["reason"])
        self.assertFalse(self.table().is_publish)
        self.assertFalse(self.table().topics.exists())

    def test_an_unknown_embargo_period_is_refused(self):
        """The old path ignored it and published without touching the
        embargo."""
        self.make_publishable()
        response = self.publish(duration="2_years", exp_code=400)
        self.assertIn("2_years", response["reason"])
        self.assertFalse(self.table().is_publish)

    def test_a_table_failing_the_publish_gate_is_refused(self):
        response = self.publish(exp_code=400)
        self.assertIn("Fails the Publish gate", response["reason"])
        self.assertFalse(self.table().is_publish)

    def test_publishing_without_an_embargo_keeps_the_one_there(self):
        """As before: only an explicit ``none`` lifts an embargo."""
        self.make_publishable()
        self.publish(duration="1_year")
        until = Embargo.objects.get(table=self.table()).date_ended
        self.publish(topic="grid")
        self.assertEqual(Embargo.objects.get(table=self.table()).date_ended, until)
        self.publish(topic="grid", duration="none")
        self.assertFalse(Embargo.objects.filter(table=self.table()).exists())

    def test_a_published_table_can_be_published_under_another_topic(self):
        """The dashboard leaves published Tables out of a publish; the API
        keeps adding a Topic, its only way to do that."""
        self.make_publishable()
        self.publish()
        self.publish(topic="grid", exp_res={})
        self.assertEqual(
            sorted(self.table().topics.values_list("name", flat=True)),
            ["grid", TOPIC_SCENARIO],
        )

    def test_the_permission_answers_are_unchanged(self):
        self.make_publishable()
        self.publish(auth=False, exp_code=401)
        self.publish(auth=self.other_token, exp_code=403)
        self.assertFalse(self.table().is_publish)


class UnpublishThroughTheServiceTests(ActionAPITestCase):
    def test_unpublishing_answers_an_empty_body_and_logs_via_api(self):
        self.make_publishable()
        self.publish()
        with self.assertLogs(LOGGER) as logs, self.captureOnCommitCallbacks(
            execute=True
        ):
            self.api_req("post", path="unpublish", exp_res={})
        self.assertFalse(self.table().is_publish)
        (line,) = logs.output
        self.assertIn("action=unpublish", line)
        self.assertIn("via=api", line)

    def test_unpublishing_a_draft_still_succeeds_and_writes_nothing(self):
        with self.assertNoLogs(LOGGER), self.captureOnCommitCallbacks(execute=True):
            self.api_req("post", path="unpublish", exp_res={})
        self.assertFalse(self.table().is_publish)

    def test_the_permission_answers_are_unchanged(self):
        self.api_req("post", path="unpublish", auth=False, exp_code=401)
        self.api_req("post", path="unpublish", auth=self.other_token, exp_code=403)


class DeleteThroughTheServiceTests(ActionAPITestCase):
    def tearDown(self):
        if self.table() is None:
            # the base class drops its table on teardown and needs it there
            self.create_table(self.test_structure)
        super().tearDown()

    def test_deleting_answers_an_empty_body_and_logs_via_api(self):
        with self.assertLogs(LOGGER) as logs:
            self.api_req("delete", exp_res={})
        self.assertIsNone(self.table())
        self.api_req("get", exp_code=404)
        (line,) = logs.output
        self.assertIn("action=delete", line)
        self.assertIn("via=api", line)
        self.assertIn("published=no drop=ok", line)

    def test_a_published_table_is_deleted_without_a_typed_confirmation(self):
        """Whether the API should guard deleting a published Table is a
        platform rule outside spec #2551; the dashboard's typed confirmation
        is answered by the name in the address."""
        self.make_publishable()
        self.publish()
        self.api_req("delete", exp_res={})
        self.assertIsNone(self.table())

    def test_a_failed_drop_is_named_never_plain_success(self):
        with mock.patch.object(
            Table, "drop_oedb_table", side_effect=RuntimeError("locked")
        ), self.assertLogs(LOGGER, "WARNING") as logs:
            response = self.api_req("delete", exp_code=500)
        self.assertIn(self.test_table, response["reason"])
        self.assertIsNone(self.table())
        self.assertIn("drop=failed", logs.output[0])
        # the OEDB table is still there; drop it so the teardown can rebuild
        self.empty_test_schema()

    def test_the_view_does_not_run_the_service_inside_a_transaction(self):
        """Delete's transaction is durable: inside another one it would
        raise. Django's TestCase switches that check off, so this looks for
        any atomic block that is not the test case's own."""
        seen = []

        def execute(*args, **kwargs):
            seen.extend(
                block
                for block in connection.atomic_blocks
                if not getattr(block, "_from_testcase", False)
            )
            return table_actions.Outcome(table_actions.DELETE, [], {})

        with mock.patch.object(table_actions, "execute", side_effect=execute):
            self.api_req("delete", exp_res={})
        self.assertEqual(seen, [])

    def test_the_permission_answers_are_unchanged(self):
        self.api_req("delete", auth=False, exp_code=401)
        self.api_req("delete", auth=self.other_token, exp_code=403)
        self.assertIsNotNone(self.table())


class RefusalMappingTests(ActionAPITestCase):
    """The service refuses whole when a Table is no longer allowed once it
    holds the lock; the API answers that as it always answered the same
    situation before the lock."""

    def refuse(self, reason):
        check = table_actions.Preflight(table_actions.UNPUBLISH, 1, [], [])
        refused = [table_actions.LeftOut(reason, [self.test_table])]
        return mock.patch.object(
            table_actions,
            "execute",
            side_effect=table_actions.ActionRefused(check, refused),
        )

    def test_a_role_lost_meanwhile_is_a_403(self):
        refusal = table_actions.ROLE_GATES[table_actions.UNPUBLISH].refusal
        with self.refuse(refusal):
            response = self.api_req("post", path="unpublish", exp_code=403)
        self.assertEqual(response, {"reason": "Permission denied"})

    def test_a_table_gone_meanwhile_is_a_404(self):
        def gone(*args, **kwargs):
            Table.objects.filter(name=self.test_table).update(name="gone_meanwhile")
            raise table_actions.ActionRefused(
                table_actions.Preflight(table_actions.UNPUBLISH, 1, [], []),
                [table_actions.LeftOut(table_actions.NOT_YOURS, [self.test_table])],
            )

        with mock.patch.object(table_actions, "execute", side_effect=gone):
            response = self.api_req("post", path="unpublish", exp_code=404)
        self.assertEqual(response, {"reason": "Table does not exist"})
        Table.objects.filter(name="gone_meanwhile").update(name=self.test_table)

    def test_a_table_without_a_role_is_a_403(self):
        """The service says "Not one of your tables" for both, so as not to
        reveal which Tables exist; the API tells them apart, as its
        permission decorators always have."""
        with self.refuse(table_actions.NOT_YOURS):
            response = self.api_req("post", path="unpublish", exp_code=403)
        self.assertEqual(response, {"reason": "Permission denied"})

    def test_any_other_refusal_is_a_400_naming_it(self):
        with self.refuse(table_actions.ALREADY_PUBLISHED):
            response = self.api_req("post", path="unpublish", exp_code=400)
        self.assertIn(table_actions.ALREADY_PUBLISHED, response["reason"])
