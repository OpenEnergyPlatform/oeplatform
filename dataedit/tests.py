"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later

"""  # noqa: 501

import logging
from typing import cast
from urllib.parse import urlencode

from django.http import HttpResponse, HttpResponseRedirect
from django.test import TestCase
from django.urls import reverse
from oemetadata.v2.v20.example import OEMETADATA_V20_EXAMPLE

from api.services.permissions import assign_table_holder
from api.services.table_creation import TableCreationOrchestrator
from base.tests import get_app_reverse_lookup_names_and_kwargs
from dataedit.models import PeerReview, PeerReviewManager, Table, Tag
from login.models import myuser as User
from oeplatform.settings import IS_TEST, SCHEMA_DEFAULT_TEST_SANDBOX


# replicated functionality from dataedit migration 0033
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
    """Call all (most) views (after creation of some test data)"""

    kwargs_w_table = {"table": "test_table", "schema": SCHEMA_DEFAULT_TEST_SANDBOX}
    kwargs_wo_table = {"schema": SCHEMA_DEFAULT_TEST_SANDBOX}

    @classmethod
    def setUpClass(cls):
        super(TestCase, cls).setUpClass()
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

        cls.tag = Tag.objects.create(name="tag1")

        # create test PeerReview # TODO: not sure how to do this correctly
        cls.peerreview = PeerReview.objects.create(
            table=cls.table.name, reviewer=cls.user1, review={}
        )
        PeerReviewManager.objects.create(opr=cls.peerreview)

    @classmethod
    def tearDownClass(cls):
        cls.peerreview.delete()
        cls.orchestrator.drop_table(
            schema=cls.kwargs_w_table["schema"],
            table=cls.kwargs_w_table["table"],
        )
        cls.user1.delete()
        super(TestCase, cls).tearDownClass()

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

    def test_views(self):
        """Call all (most) views that can be found with reverse lookup.
        We only test method GET
        """
        default_kwargs = {
            "schema": SCHEMA_DEFAULT_TEST_SANDBOX,
            "table": self.table.name,
            "review_id": self.peerreview.pk,
            "tag_pk": self.tag.pk,
            "maptype": "latlon",
        }
        for name, kwarg_names in sorted(
            get_app_reverse_lookup_names_and_kwargs("dataedit").items()
        ):
            if name in {
                "dataedit:tags-add",
                "dataedit:tags-set",
                "dataedit:table-view-save",
                "dataedit:table-view-set-default",
                "dataedit:table-view-delete-default",
            }:
                # ignore these (POST)
                continue

            kwargs = {k: default_kwargs[k] for k in kwarg_names}

            url = reverse(name, kwargs=kwargs)
            # also: pass kwargs as query data for views that use request.GET
            query_string = urlencode(default_kwargs)
            url += f"?{query_string}"

            expected_status = 200
            self.client.force_login(self.user1)

            try:

                resp = self.client.get(url)
                self.assertEqual(resp.status_code, expected_status)
            except Exception:
                logging.error("Test failed for url: (%s) %s", name, url)
                raise
