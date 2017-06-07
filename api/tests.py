import json

from django.test import TestCase, Client

# Create your tests here.
from api import actions


class APITestCase(TestCase):
    test_schema = 'schema1'
    test_table = 'population2'

    content_data = []

    structure_data = {
        "constraints": [
            {
                "constraint_type": "PRIMARY KEY",
                "constraint_name": "test_enviroment_population2_id_pkey",
                "constraint_parameter": "id",
                "reference_table": None,
                "reference_column": None
            }
        ],
        "columns": [
            {
                "name": "id",
                "data_type": "integer",
                "is_nullable": "NO",
                "character_maximum_length": None
            },
            {
                "name": "name",
                "data_type": "character varying",
                "is_nullable": "YES",
                "character_maximum_length": 50
            }, {
                "name": "address",
                "data_type": "character varying",
                "is_nullable": "YES",
                "character_maximum_length": 150
            }
        ]
    }

    def setUp(self):
        self.client = Client()

    def checkStructure(self):
        response = self.client.get(
            '/api/v0/schema/{schema}/tables/{table}/'.format(schema=self.test_schema, table=self.test_table))
        body = json.loads(response.content.decode("utf-8"))

        self.assertEqual(body['schema'], self.test_schema, "Schema does not match.")
        self.assertEqual(body['name'], self.test_table, "Table does not match.")

        for column in self.structure_data['columns']:
            for key in column:
                # name is a programmer-introduced key.
                # We are able to use a list instead of a dictonary to get better iteration possibilities.
                if key == 'name':
                    continue

                value = column[key]
                self.assertEqual(value, body['columns'][column['name']][key],
                                 "Key '{key}' does not match.".format(key=key))

        self.assertEqual(response.status_code, 200, "Status Code is not 200.")

    def checkContent(self):

        response = self.client.get(
            '/api/v0/schema/{schema}/tables/{table}/rows/'.format(schema=self.test_schema, table=self.test_table))

        body = json.loads(response.content.decode("utf-8"))

        self.assertEqual(body, self.content_data)

    def test_a_initializationDatabase(self):
        actions.perform_sql("DROP SCHEMA IF EXISTS schema1 CASCADE")
        actions.perform_sql("DROP SCHEMA IF EXISTS schema2 CASCADE")
        actions.perform_sql("DROP SCHEMA IF EXISTS schema3 CASCADE")

        actions.perform_sql("CREATE SCHEMA schema1")
        actions.perform_sql("CREATE SCHEMA schema2")
        actions.perform_sql("CREATE SCHEMA schema3")

    def test_create_table(self):

        c_basic_resp = self.client.put(
            '/api/v0/schema/{schema}/tables/{table}/'.format(schema=self.test_schema, table=self.test_table),
            json.dumps(self.structure_data),
            format='json')

        self.assertEqual(c_basic_resp.status_code, 200, 'Status Code is not 200.')
        self.checkStructure()

    def test_modify_table(self):



        data_column = {"type": "column", "name": "number", "data_type": "int", "is_nullable": "NO",
                       "character_maximum_length": None}
        data_constraint = {"type": "constraint", "action": "ADD", "constraint_type": "UNIQUE",
                           "constraint_name": "number_unique", "constraint_parameter": "number"}

        j_data_column = json.dumps(data_column)
        j_data_constraint = json.dumps(data_constraint)

        headerInfo = {'content-type': 'application/json'}

        c_column_resp = self.client.post(
            '/api/v0/schema/{schema}/tables/{table}/'.format(schema=self.test_schema, table=self.test_table),
            data=data_column)

        c_constraint_resp = self.client.post(
            '/api/v0/schema/{schema}/tables/{table}/'.format(schema=self.test_schema, table=self.test_table),
            data=data_constraint)

        self.assertEqual(c_column_resp.status_code, 200, 'Status Code is not 200.')
        self.assertEqual(c_constraint_resp.status_code, 200, 'Status Code is not 200.')

    def test_insert_data(self):

        insert_data = [{"columnData":
            {
                "id": 1,
                "name": "Random Name",
                "address": "Random Address 1234"
            }
        }, {"columnData":
            {
                "id": 2,
                "name": "Paul Erik Sebasitian",
                "address": "Irgendwo auf dem Werder 5"
            }
        }]

        for row in insert_data:
            response = self.client.put(
                '/api/v0/schema/{schema}/tables/{table}/rows/'.format(schema=self.test_schema, table=self.test_table),
                data=json.dumps(row))

            self.assertEqual(response.status_code, 200, "Status Code is not 200.")
            self.content_data.append(row['columnData'])

        self.checkContent()

    def test_modify_data(self):
        pass

    def test_remove_data(self):
        pass
