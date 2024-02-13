from api.tests import APITestCaseWithTable


class Test1548(APITestCaseWithTable):
    """Delete a row using the http-api leads to server error
    if table includes not nullable fields"""

    test_structure = {
        "columns": [
            {"name": "name", "data_type": "varchar(18)", "is_nullable": False},
        ]
    }
    test_data = [{"name": "name1"}, {"name": "name2"}]

    def test1548(self):
        # id=1 was generated automatically
        res = self.api_req("GET", path="rows/1")
        self.assertEqual(res["id"], 1)
        # now we delete it
        self.api_req("DELETE", path="rows/1")
