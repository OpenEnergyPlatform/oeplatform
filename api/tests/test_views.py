"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import reverse

from api.tests import APITestCaseWithTable
from base.tests import get_app_reverse_lookup_names_and_kwargs


class TestViewsApi(APITestCaseWithTable):
    """Call all (most) views (after creation of some test data)"""

    test_data = [{"id": 1}, {"id": 2}]

    @classmethod
    def setUpClass(cls):
        super(APITestCaseWithTable, cls).setUpClass()
        # create test user

    @classmethod
    def tearDownClass(cls):
        super(APITestCaseWithTable, cls).tearDownClass()

    def test_views(self):
        """Call all (most) views that can be found with reverse lookup.
        We only test method GET
        """

        default_kwargs = {
            "schema": self.test_schema,
            "table": self.test_table,
            "row_id": 1,
            "column": "id",
            "column_id": 1,
            "to_schema": self.test_schema,
        }

        for name, kwarg_names in sorted(
            get_app_reverse_lookup_names_and_kwargs("api").items()
        ):
            if ":advanced-" in name:
                # advanced are all POST
                continue
            if name in {
                "api:add-scenario-datasets",
                "api:api_rows_new",
                "api:move",
                "api:move_publish",
                "api:oekg-sparql-http-api",
                "api:oeo-search",  # only when USE_LOEP
                "api:oevkg-query",  # only when USE_ONTOP
            }:
                continue

            kwargs = {k: default_kwargs[k] for k in kwarg_names}
            url = reverse(name, kwargs=kwargs)

            self.client.force_login(self.user)  # TODO: only some need auth

            resp = self.client.get(path=url)
            self.assertEqual(resp.status_code, 200)
