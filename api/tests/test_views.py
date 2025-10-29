"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from base.tests import TestViewsTestCase


class TestViewsApi(TestViewsTestCase):
    """Call all (most) views (after creation of some test data)"""

    @classmethod
    def setUpClass(cls):
        super(TestViewsApi, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(TestViewsApi, cls).tearDownClass()

    def test_views(self):
        """Call all (most) views that can be found with reverse lookup.
        We only test method GET

        NOTE: we dont test advanced api, and also only those without a table,
        those are tested elsewhere
        """

        # "api:oekg-sparql-http-api",
        # "api:oeo-search",  # only when USE_LOEP
        # "api:oevkg-query",  # only when USE_ONTOP

        self.get("api:grpprop", logged_in=True)
        self.get("api:usrprop", logged_in=True)
        self.get("api:list-framework-factsheets")
        self.get("api:list-model-factsheets")
        self.get("api:list-scenario-datasets")
        self.get("api:table-sizes")
