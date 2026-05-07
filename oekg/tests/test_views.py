"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from base.tests import TestViewsTestCase


class TestViewsOekg(TestViewsTestCase):
    """Call all (most) views"""

    def test_views(self):
        """Call all (most) views that can be found with reverse lookup.
        We only test method GET
        """
        # "oekg:sparql_endpoint": POST
        # "oekg:filter_oekg_by_scenario_bundles_attributes": POST

        self.get("oekg:main")
        self.get("oekg:sparql_endpoint_info")
