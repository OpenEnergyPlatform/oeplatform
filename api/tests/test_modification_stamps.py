"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

When a Table's content last changed (#2557, spec #2551): every Modification
stamps one of two halves, ``data_modified`` or ``metadata_modified``, and
status changes stamp neither. Driven through the write paths a client uses,
and asserted on what the database holds afterwards.

The queued column and constraint changes are the one exception: the queue's
own apply (``apply_queued_column``) raises before it reaches the change
(``get_column_changes`` reads a column ``api_columns`` does not have, #2490),
so no request can get there. Its two writers are called directly instead.
"""  # noqa: 501

from copy import deepcopy

from django.urls import reverse
from django.utils import timezone
from oemetadata.v2.v20.example import OEMETADATA_V20_EXAMPLE

from api.actions import table_change_column, table_change_constraint
from api.error import APIError
from api.tests import APITestCaseWithTable
from dataedit.models import Table
from login.permissions import WRITE_PERM
from oeplatform.settings import TOPIC_SCENARIO


class StampTestCase(APITestCaseWithTable):
    test_table = "test_table_modification_stamps"

    def setUp(self):
        self.started = timezone.now()
        super().setUp()

    def stamps(self):
        table = Table.objects.get(name=self.test_table)
        return table.data_modified, table.metadata_modified

    def clear(self):
        """Forget every stamp, so the next write is the only one that can
        have set one."""
        Table.objects.filter(name=self.test_table).update(
            data_modified=None, metadata_modified=None
        )

    def assertJustNow(self, stamp):
        self.assertIsNotNone(stamp)
        self.assertTrue(self.started <= stamp <= timezone.now(), stamp)

    def assertStamped(self, data=False, metadata=False):
        data_modified, metadata_modified = self.stamps()
        for stamped, stamp in ((data, data_modified), (metadata, metadata_modified)):
            if stamped:
                self.assertJustNow(stamp)
            else:
                self.assertIsNone(stamp)

    def write_rows(self):
        self.api_req(
            "post",
            path="rows/new",
            data={"query": [{"id": 1, "name": "one"}]},
            exp_code=201,
        )


class MetadataHalfTests(StampTestCase):
    def test_creating_a_table_stamps_its_metadata_only(self):
        """Creation writes metadata (the template, if none was sent) through
        the one metadata write path; it writes no data."""
        self.assertStamped(metadata=True)

    def test_a_metadata_write_stamps_the_metadata_half(self):
        self.clear()
        self.api_req("post", path="meta/", data=deepcopy(OEMETADATA_V20_EXAMPLE))
        self.assertStamped(metadata=True)

    def test_the_stamp_moves_with_every_metadata_write(self):
        self.api_req("post", path="meta/", data=deepcopy(OEMETADATA_V20_EXAMPLE))
        _, first = self.stamps()
        self.api_req("post", path="meta/", data=deepcopy(OEMETADATA_V20_EXAMPLE))
        _, second = self.stamps()
        self.assertGreater(second, first)

    def test_refused_metadata_stamps_nothing(self):
        self.clear()
        self.api_req(
            "post", path="meta/", data={"resources": "not a list"}, exp_code=400
        )
        self.assertStamped()


class DataHalfTests(StampTestCase):
    def test_applying_new_rows_stamps_the_data_half(self):
        self.clear()
        self.write_rows()
        self.assertStamped(data=True)

    def test_deleting_a_row_stamps_the_data_half(self):
        self.write_rows()
        self.clear()
        self.api_req("delete", path="rows/1")
        self.assertStamped(data=True)

    def test_a_bulk_upload_stamps_the_data_half(self):
        self.clear()
        response = self.client.post(
            f"/api/v0/tables/{self.test_table}/bulk-upload/?delimiter=comma",
            data=b"id,name\n1,one\n2,two\n",
            content_type="text/csv",
            HTTP_AUTHORIZATION=f"Token {self.token}",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertStamped(data=True)

    def test_a_failed_bulk_upload_stamps_nothing(self):
        self.clear()
        response = self.client.post(
            f"/api/v0/tables/{self.test_table}/bulk-upload/?delimiter=comma",
            data=b"id,no_such_column\n1,one\n",
            content_type="text/csv",
            HTTP_AUTHORIZATION=f"Token {self.token}",
        )
        self.assertEqual(response.status_code, 400, response.content)
        self.assertStamped()

    def test_adding_a_column_stamps_the_data_half(self):
        self.clear()
        self.api_req(
            "put",
            path="columns/added",
            data={"query": {"data_type": "varchar", "character_maximum_length": 30}},
            exp_code=201,
        )
        self.assertStamped(data=True)

    def test_altering_a_column_stamps_the_data_half(self):
        self.clear()
        self.api_req(
            "post",
            path="columns/name",
            data={"query": {"data_type": "text"}},
        )
        self.assertStamped(data=True)

    def test_an_alteration_naming_nothing_to_alter_stamps_nothing(self):
        self.clear()
        self.api_req("post", path="columns/name", data={"query": {"comment": "x"}})
        self.assertStamped()

    def test_a_queued_column_change_stamps_the_data_half(self):
        """A new column: the queue's alter branch cannot run on any existing
        column (it reads ``is_nullable`` as text, and it is a bool)."""
        self.clear()
        result = table_change_column(
            {
                "c_table": self.test_table,
                "column_name": "queued",
                "new_name": None,
                "data_type": "text",
            }
        )
        self.assertTrue(result["success"])
        self.assertStamped(data=True)

    def test_a_queued_change_that_fails_stamps_nothing(self):
        self.clear()
        with self.assertRaises(APIError):
            table_change_column(
                {
                    "c_table": self.test_table,
                    "column_name": "queued",
                    "new_name": None,
                    "data_type": "no_such_type",
                }
            )
        self.assertStamped()

    def test_a_queued_constraint_change_stamps_the_data_half(self):
        self.clear()
        result = table_change_constraint(
            {
                "c_table": self.test_table,
                "action": "DROP",
                "constraint_name": f"{self.test_table}_pkey",
            }
        )
        self.assertTrue(result["success"])
        self.assertStamped(data=True)


class StatusChangesStampNothingTests(StampTestCase):
    """Publish, unpublish, embargo and role changes are status, not content:
    each has its own column, and counting them would move a Table up the
    list for something nobody changed in it."""

    def setUp(self):
        super().setUp()
        # the license the Publish gate wants, written before the stamps go
        self.api_req("post", path="meta/", data=deepcopy(OEMETADATA_V20_EXAMPLE))
        self.clear()

    def publish(self, embargo="none"):
        self.api_req(
            "post",
            path=f"move_publish/{TOPIC_SCENARIO}/",
            data={"embargo": {"duration": embargo}},
        )

    def test_publishing(self):
        self.publish()
        self.assertTrue(Table.objects.get(name=self.test_table).is_publish)
        self.assertStamped()

    def test_publishing_under_an_embargo(self):
        self.publish(embargo="6_months")
        self.assertTrue(Table.objects.get(name=self.test_table).embargos.exists())
        self.assertStamped()

    def test_unpublishing(self):
        self.publish()
        self.clear()
        self.api_req("post", path="unpublish")
        self.assertFalse(Table.objects.get(name=self.test_table).is_publish)
        self.assertStamped()

    def test_granting_a_role(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("dataedit:table-permission", kwargs={"table": self.test_table}),
            {"mode": "add_user", "name": self.other_user.name, "level": WRITE_PERM},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Table.objects.get(name=self.test_table)
            .userpermission_set.filter(holder=self.other_user)
            .exists()
        )
        self.assertStamped()
