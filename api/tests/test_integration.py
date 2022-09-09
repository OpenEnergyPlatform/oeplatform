from api.tests import APITestCase


class IntegrationTestCase(APITestCase):
    content_data = []

    structure_data = {
        "constraints": [
            {
                "constraint_type": "PRIMARY KEY",
                "constraint_name": "test_enviroment_population2_id_pkey",
                "constraint_parameter": "id",
                "reference_table": None,
                "reference_column": None,
            }
        ],
        "columns": [
            {
                "name": "id",
                "data_type": "bigserial",
                "is_nullable": False,
                "character_maximum_length": None,
            },
            {
                "name": "name",
                "data_type": "character varying",
                "is_nullable": True,
                "character_maximum_length": 50,
            },
            {
                "name": "address",
                "data_type": "character varying",
                "is_nullable": True,
                "character_maximum_length": 150,
            },
        ],
    }

    def test(self):
        self.step_create_table()
        self.step_modify_table()
        self.step_insert_data()
        self.step_modify_data()
        self.step_remove_data()

    def setUp(self):
        pass

    def checkStructure(self):
        body = self.api_req("get")

        self.assertEqual(body["schema"], self.test_schema, "Schema does not match.")
        self.assertEqual(body["name"], self.test_table, "Table does not match.")

        for column in self.structure_data["columns"]:
            for key in column:
                # name is a programmer-introduced key.
                # We are able to use a list instead of a dictonary to get
                # better iteration possibilities.
                if key == "name":
                    continue
                if key == "data_type" and column[key] == "bigserial":
                    column[key] = "bigint"
                value = column[key]
                self.assertEqual(
                    value,
                    body["columns"][column["name"]][key],
                    "Key '{key}' does not match.".format(key=key),
                )

    def checkContent(self):
        self.api_req("get", path="rows/", exp_res=self.content_data)

    def step_create_table(self):
        self.api_req("put", data={"query": self.structure_data})
        self.checkStructure()

    def step_modify_table(self):

        data_column = {
            "type": "column",
            "name": "number",
            "data_type": "int",
            "is_nullable": "NO",
            "character_maximum_length": None,
        }
        data_constraint = {
            "type": "constraint",
            "action": "ADD",
            "constraint_type": "UNIQUE",
            "constraint_name": "number_unique",
            "constraint_parameter": "number",
        }

        self.api_req("post", data=data_column)
        self.api_req("post", data=data_constraint)

    def step_insert_data(self):

        insert_data = [
            {
                "query": {
                    "id": 1,
                    "name": "Random Name",
                    "address": "Random Address 1234",
                }
            },
            {
                "query": {
                    "id": 2,
                    "name": "Paul Erik Sebasitian",
                    "address": "Irgendwo auf dem Werder 5",
                }
            },
        ]

        for row in insert_data:
            rid = row["query"]["id"]
            self.api_req("put", path=f"rows/{rid}", data=row)
            self.content_data.append(row["query"])

        self.checkContent()

    def step_modify_data(self):
        pass

    def step_remove_data(self):
        pass
