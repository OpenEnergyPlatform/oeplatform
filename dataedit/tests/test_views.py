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
from django.urls import reverse

from base.tests import TestViewsTestCase
from dataedit.models import PeerReview, PeerReviewManager, Table, Tag


class TestViewsDataedit(TestViewsTestCase):
    """Call all (most) views (after creation of some test data)"""

    table_name = "test_table"

    @classmethod
    def setUpClass(cls):
        super(TestViewsDataedit, cls).setUpClass()

        # create a test table
        # ensure test table does not exist
        cls.table = Table.create_with_oedb_table(
            is_sandbox=True,  # IMPORTANT for test
            name=cls.table_name,
            user=cls.user,
            column_definitions=[],
            constraints_definitions=[],
        )

        cls.tag = Tag.objects.create(name="tag1")

        # create test PeerReview # TODO: not sure how to do this correctly
        cls.peerreview = PeerReview.objects.create(
            table=cls.table.name, reviewer=cls.user, review={}
        )
        PeerReviewManager.objects.create(opr=cls.peerreview)

    @classmethod
    def tearDownClass(cls):
        cls.peerreview.delete()
        cls.table.delete()
        super(TestViewsDataedit, cls).tearDownClass()

    def test_views_wizard(self):
        # GET without table
        url = reverse("dataedit:wizard_create")

        # try without logging in -> redirect to login
        response = self.client.get(url)
        self.assert_redirect_to_login(response)

        # with logged in user
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # GET with table
        url = reverse("dataedit:wizard_upload", kwargs={"table": self.table_name})

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
        table = "test_table"

        self.get("dataedit:topic-list")
        self.get("dataedit:topic-list")
        self.get("dataedit:meta_edit", kwargs={"table": table})
        self.get(
            "dataedit:metadata-widget",
            query={"table": table},
        )
        self.get("dataedit:oemetabuilder")
        self.get(
            "dataedit:peer_review_contributor",
            kwargs={"table": table, "review_id": 1},
        )
        self.get(
            "dataedit:peer_review_create",
            kwargs={"table": table},
        )
        self.get(
            "dataedit:peer_review_reviewer",
            kwargs={"table": table, "review_id": 1},
        )
        self.get("dataedit:table-graph", kwargs={"table": table})
        self.get(
            "dataedit:table-map",
            kwargs={"table": table, "maptype": "latlon"},
        )
        self.get(
            "dataedit:table-permission",
            kwargs={"table": table},
        )
        self.get("dataedit:tables-in-topic-in-topic", kwargs={"topic": "scenario"})
        self.get("dataedit:tags")
        self.get("dataedit:tags-edit", kwargs={"tag_pk": "tag1"})
        self.get("dataedit:tags-new")
        self.get("dataedit:topic-list")
        self.get("dataedit:view", kwargs={"table": table})
        self.get("dataedit:wizard_create")
        self.get(
            "dataedit:wizard_upload",
            kwargs={"table": table},
        )
