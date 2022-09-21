from api.tests import APITestCaseWithTable


class Test270(APITestCaseWithTable):
    test_data = [{"name": "Hans"}, {"name": "Petra"}, {"name": "Dieter"}]

    def test_270(self):
        self.api_req(
            "get",
            path="rows/?where=name<>Hans&where=name<>Dieter",
            exp_res=[{"name": "Petra", "id": 2, "address": None, "geom": None}],
        )
