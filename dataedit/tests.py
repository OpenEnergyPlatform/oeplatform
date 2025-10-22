"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later

"""  # noqa: 501

from typing import cast

from django.http import HttpResponse, HttpResponseRedirect
from django.test import TestCase
from django.urls import reverse
from oemetadata.v2.v20.example import OEMETADATA_V20_EXAMPLE

from api.services.permissions import assign_table_holder
from api.services.table_creation import TableCreationOrchestrator
from dataedit.models import PeerReview, Table
from login.models import myuser as User
from oeplatform.settings import IS_TEST, SCHEMA_DEFAULT_TEST_SANDBOX


# replicated functionality form dataedit migration 0033
# avoid setting up full migration test framework
def populate_peerreview_oemetadata():
    for review in PeerReview.objects.all():
        if not review.oemetadata or review.oemetadata == {}:
            # Logic to find a matching value from TableModel.
            table = Table.objects.filter(name=review.table).first()
            if table:
                review.oemetadata = table.oemetadata
                review.save()


class MigrationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        table = Table.objects.create(
            name="test_table",
            oemetadata=OEMETADATA_V20_EXAMPLE,
        )

        test_contributor = User.objects.create(
            name="test_user_contributor", email="contributor@test.de"
        )
        test_reviewer = User.objects.create(
            name="test_user_reviewer", email="reviewer@test.de"
        )

        PeerReview.objects.create(
            # Make sure this assignment matches your model's expectations
            table=table.name,
            contributor=test_contributor,
            reviewer=test_reviewer,
            # Simulate a record that needs migration
            oemetadata={},
        )

    def test_migration(self):
        # Apply the migration
        # executor = MigrationExecutor(connection)
        # app = "dataedit"
        # migration_name = "0033_peerreview_oemetadata"
        # executor.migrate([(app, migration_name)])

        # Make sure at least one PeerReview instance exists for testing
        self.assertTrue(PeerReview.objects.exists(), "PeerReview instance should exist")

        # Re-fetch records from the database
        review = PeerReview.objects.first()
        if not review:
            raise Exception("no review")
        self.assertEqual(review.oemetadata, {})

        populate_peerreview_oemetadata()

        # Update Re-fetch records from the database
        review = PeerReview.objects.first()
        if not review:
            raise Exception("no review")

        # Since the 'oemetadata' field is added by the migration, it will exist here
        # Now perform your checks on 'oemetadata'
        self.assertEqual(review.oemetadata, OEMETADATA_V20_EXAMPLE)

    def test_migration_rollback(self):
        # Implement if needed
        pass


class TestViews(TestCase):
    """call all (most) views"""

    kwargs_w_table = {"table": "test_table", "schema": SCHEMA_DEFAULT_TEST_SANDBOX}
    kwargs_wo_table = {"schema": SCHEMA_DEFAULT_TEST_SANDBOX}

    @classmethod
    def setUpClass(cls):
        # ensure IS_TEST is set correctly
        if not IS_TEST:
            raise Exception("IS_TEST is not True")

        # create test user
        cls.user1 = User.objects.create_user(  # type: ignore
            name="test", email="test@test.test", affiliation="test"
        )

        # create a test table
        cls.orchestrator = TableCreationOrchestrator()
        # ensure test table doesnot exist
        cls.orchestrator.drop_table(
            schema=cls.kwargs_w_table["schema"],
            table=cls.kwargs_w_table["table"],
        )
        cls.table = cls.orchestrator.create_table(
            schema=cls.kwargs_w_table["schema"],
            table=cls.kwargs_w_table["table"],
            column_defs=[],
            constraint_defs=[],
        )
        assign_table_holder(
            cls.user1,
            schema=cls.kwargs_w_table["schema"],
            table=cls.kwargs_w_table["table"],
        )

    @classmethod
    def tearDownClass(cls):

        cls.orchestrator.drop_table(
            schema=cls.kwargs_w_table["schema"],
            table=cls.kwargs_w_table["table"],
        )

    def test_views_wizard_TODO_UNFINISHED(self):
        # GET without table
        url = reverse("dataedit:wizard_create")

        # try without logging in -> redirect to login
        response = self.client.get(url)
        self.assert_redirect_to_login(response)

        # with logged in user
        self.client.force_login(self.user1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # GET with table
        url = reverse("dataedit:wizard_upload", kwargs=self.kwargs_w_table)

        # try without logging in -> redirect to login
        response = self.client.get(url)

    def assert_redirect_to_login(self, response: HttpResponse):
        self.assertEqual(response.status_code, 302)
        self.assertTrue(isinstance(response, HttpResponseRedirect))
        response = cast(HttpResponseRedirect, response)
        self.assertTrue("login" in response.url)
