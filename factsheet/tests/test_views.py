"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from base.tests import TestViewsTestCase


class TestViewsFactsheet(TestViewsTestCase):
    """Call all (most) views"""

    def test_views(self):
        """Call all (most) views that can be found with reverse lookup.
        We only test method GET
        """

        # "factsheet:add",  # requires POST
        # "factsheet:delete",  # requires POST
        # "factsheet:test-query",  # TODO: test query does not work
        # "factsheet:all",  # TODO:  Temporary failure in name resolution>
        # "factsheet:all-in-jsonld",  # TODO ???
        # "factsheet:filter_bundles_view",  # TODO ???
        # "factsheet:get",  # TODO ???
        # "factsheet:get-entities-by-type",  # TODO ???
        # "factsheet:get-scenarios",  # TODO ???
        # "factsheet:populate-factsheets-elements",  # TODO ???

        self.get("factsheet:add-a-fact")
        self.get("factsheet:add-entities")
        self.get("factsheet:all-in-turtle")
        self.get("factsheet:bundle-id-page", args=["SOME_UID"])
        self.get("factsheet:check_ownership", kwargs={"bundle_id": "new"})
        self.get("factsheet:compare", args=["SOME_UID"])
        self.get("factsheet:factsheets_index")
        self.get("factsheet:get-oekg-modifications")
        self.get("factsheet:index")
        self.get("factsheet:is-logged-in")
        self.get("factsheet:oekg-history", args=["SOME_UID"])
        self.get("factsheet:oekg-modifications", args=["SOME_UID"])
        self.get("factsheet:update")
        self.get("factsheet:update-an-entity")
