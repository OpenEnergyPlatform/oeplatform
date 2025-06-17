# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from api.tests import APITestCaseWithTable


class Test270(APITestCaseWithTable):
    test_data = [{"name": "Hans"}, {"name": "Petra"}, {"name": "Dieter"}]

    def test_270(self):
        self.api_req(
            "get",
            path="rows/?where=name<>Hans&where=name<>Dieter",
            exp_res=[{"name": "Petra", "id": 2, "address": None, "geom": None}],
        )
