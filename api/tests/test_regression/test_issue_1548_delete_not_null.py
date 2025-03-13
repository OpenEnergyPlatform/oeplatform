# SPDX-FileCopyrightText: 2024 Christian Winger <wingechr>
# SPDX-FileCopyrightText: oeplatform <https://github.com/OpenEnergyPlatform/oeplatform/>
# SPDX-License-Identifier: MIT

from api.tests import APITestCaseWithTable


class Test1548(APITestCaseWithTable):
    """Delete a row using the http-api leads to server error
    if table includes not nullable fields"""

    test_structure = {
        "columns": [
            {"name": "name", "data_type": "varchar(18)", "is_nullable": False},
            {"name": "value", "data_type": "int", "is_nullable": False},
        ]
    }
    test_data = [{"name": "name1", "value": 10}, {"name": "name2", "value": 20}]

    def test1548(self):
        self.assertEqual(len(self.api_req("GET", path="rows/")), 2)
        # id=1 was generated automatically
        res = self.api_req("GET", path="rows/1")
        self.assertEqual(res["id"], 1)
        # now we delete it (This created the error)
        self.api_req("DELETE", path="rows/1")
        # check that delete worked
        self.api_req("GET", path="rows/1", exp_code=404)
        self.assertEqual(len(self.api_req("GET", path="rows/")), 1)
