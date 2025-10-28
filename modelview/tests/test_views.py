"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging
from urllib.parse import urlencode

from django.test import TestCase
from django.urls import reverse

from base.tests import get_app_reverse_lookup_names_and_kwargs
from login.models import myuser as User
from modelview.models import Energymodel


class TestViewsModelview(TestCase):
    """Call all (most) views (after creation of some test data)"""

    @classmethod
    def setUpClass(cls):
        super(TestCase, cls).setUpClass()
        # create test user
        cls.user1 = User.objects.create_user(  # type: ignore
            name="test", email="test@test.test", affiliation="test"
        )
        cls.factsheet = Energymodel.objects.create(contact_email=[cls.user1.email])

    @classmethod
    def tearDownClass(cls):
        cls.factsheet.delete()
        cls.user1.delete()
        super(TestCase, cls).tearDownClass()

    def test_views(self):
        """Call all (most) views that can be found with reverse lookup.
        We only test method GET
        """
        default_kwargs = {"sheettype": "model", "pk": self.factsheet.pk}
        for name, kwarg_names in sorted(
            get_app_reverse_lookup_names_and_kwargs("modelview").items()
        ):

            # skip these, usually because they dont support GET
            if name in {"modelview:delete-factsheet", "modelview:update"}:
                # ignore: needs POST
                continue

            kwargs = {k: default_kwargs[k] for k in kwarg_names}
            url = reverse(name, kwargs=kwargs)

            # also: pass kwargs as query data for views that use request.GET
            url = reverse(name, kwargs=kwargs)
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
