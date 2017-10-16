from api import actions
from django.contrib.auth import get_user_model
from api.tests import APITestCase
import json

class IntegrationTestCase(APITestCase):
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
                "data_type": "bigserial",
                "is_nullable": False,
                "character_maximum_length": None
            },
            {
                "name": "name",
                "data_type": "character varying",
                "is_nullable": True,
                "character_maximum_length": 50
            }, {
                "name": "address",
                "data_type": "character varying",
                "is_nullable": True,
                "character_maximum_length": 150
            }
        ]
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
        response = self.__class__.client.get(
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
                if key == 'data_type' and column[key] == 'bigserial':
                    column[key] = 'bigint'
                value = column[key]
                self.assertEqual(value, body['columns'][column['name']][key],
                                 "Key '{key}' does not match.".format(key=key))

        self.assertEqual(response.status_code, 200, "Status Code is not 200.")

    def checkContent(self):

        response = self.__class__.client.get(
            '/api/v0/schema/{schema}/tables/{table}/rows/'.format(schema=self.test_schema, table=self.test_table))

        body = response.json()

        self.assertEqual(body, self.content_data)

    def step_create_table(self):

        c_basic_resp = self.__class__.client.put(
            '/api/v0/schema/{schema}/tables/{table}/'.format(schema=self.test_schema, table=self.test_table),
            data=json.dumps({'query': self.structure_data}),
            HTTP_AUTHORIZATION='Token %s' % self.__class__.token,
            content_type='application/json')

        self.assertEqual(c_basic_resp.status_code, 201, 'Status Code is not 201: ' + c_basic_resp.json().get('reason', 'No reason returned') )
        self.checkStructure()

    def step_modify_table(self):



        data_column = {"type": "column", "name": "number", "data_type": "int", "is_nullable": "NO",
                       "character_maximum_length": None}
        data_constraint = {"type": "constraint", "action": "ADD", "constraint_type": "UNIQUE",
                           "constraint_name": "number_unique", "constraint_parameter": "number"}

        j_data_column = json.dumps(data_column)
        j_data_constraint = json.dumps(data_constraint)

        headerInfo = {'content-type': 'application/json'}

        c_column_resp = self.__class__.client.post(
            '/api/v0/schema/{schema}/tables/{table}/'.format(schema=self.test_schema, table=self.test_table),
            data=json.dumps(data_column), HTTP_AUTHORIZATION='Token %s' % self.__class__.token,
            content_type='application/json')

        c_constraint_resp = self.__class__.client.post(
            '/api/v0/schema/{schema}/tables/{table}/'.format(schema=self.test_schema, table=self.test_table),
            data=json.dumps(data_constraint), HTTP_AUTHORIZATION='Token %s' % self.__class__.token,
            content_type='application/json')

        self.assertEqual(c_column_resp.status_code, 200, c_column_resp.get('reason', 'No reason returned'))
        self.assertEqual(c_constraint_resp.status_code, 200, 'Status Code is not 200.')

    def step_insert_data(self):

        insert_data = [{"query":
            {
                "id": 1,
                "name": "Random Name",
                "address": "Random Address 1234"
            }
        }, {"query":
            {
                "id": 2,
                "name": "Paul Erik Sebasitian",
                "address": "Irgendwo auf dem Werder 5"
            }
        }]

        for row in insert_data:
            response = self.__class__.client.put(
                '/api/v0/schema/{schema}/tables/{table}/rows/{rid}'.format(schema=self.test_schema, table=self.test_table, rid=row['query']['id']),
                data=json.dumps(row), HTTP_AUTHORIZATION='Token %s' % self.__class__.token,
            content_type='application/json')

            self.assertEqual(response.status_code, 201, "Status Code is not 201.")
            self.content_data.append(row['query'])

        self.checkContent()

    def step_modify_data(self):
        pass

    def step_remove_data(self):
        pass
