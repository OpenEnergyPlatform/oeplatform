"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from base.tests import TestViewsTestCase
from modelview.models import Energymodel


class TestViewsModelview(TestViewsTestCase):
    """Call all (most) views (after creation of some test data)"""

    def setUp(self):
        self.factsheet = Energymodel.objects.create(contact_email=[self.user.email])

    def tearDown(self):
        self.factsheet.delete()

    def test_views(self):
        """Call all (most) views that can be found with reverse lookup.
        We only test method GET
        """

        # "modelview:delete-factsheet": POST
        # "modelview:update": POST

        self.get("modelview:download", kwargs={"sheettype": "model"})
        self.get(
            "modelview:edit", kwargs={"sheettype": "model", "pk": self.factsheet.pk}
        )
        self.get("modelview:modeladd", kwargs={"sheettype": "model"})
        self.get("modelview:modellist", kwargs={"sheettype": "model"})
        self.get(
            "modelview:show-factsheet",
            kwargs={"sheettype": "model", "pk": self.factsheet.pk},
        )
