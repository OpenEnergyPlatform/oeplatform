from api.tests import APITestCaseWithTable

BAD_VALUES = [True, {}, "", "not a date", "200", "2020-30-40", "2020-01-01 WTF"]
OK_VALUES = {
    None: None,
    2020: 2020,
    "2020": "2020",
    "2020-12": "2020-12",
    "2020-12-02": "2020-12-02",
    "2020-12-2": "2020-12-02",
    "2020-10-01T10:12:13": "2020-10-01T10:12:13",
    "2020-10-01 10:12": "2020-10-01T10:12:00",
    "2020-10-01T10:12:13+0200": "2020-10-01T10:12:13+02:00",
}


class TestIssue1151ParseDate(APITestCaseWithTable):
    def test_issue_1151_parse_date(self):
        for dt_value_in in BAD_VALUES:
            meta = {"id": "test", "temporal": {"timeseries": {"start": dt_value_in}}}
            # write bad metadata: expect error
            self.api_req("post", path="meta/", data=meta, exp_code=400)

        for dt_value_in, dt_value_out in OK_VALUES.items():
            meta = {"id": "test", "temporal": {"timeseries": {"start": dt_value_in}}}
            # write good metadata
            self.api_req("post", path="meta/", data=meta)
            # read metadata back
            res = self.api_req("get", path="meta/")
            self.assertEqual(dt_value_out, res["temporal"]["timeseries"].get("start"))
