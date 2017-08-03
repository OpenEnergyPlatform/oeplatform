from . import APITestCase
from api import actions
import json

class TestRowsPut(APITestCase):

    def setUp(self):
        self.test_table = 'test_table_rows'
        self.test_schema = 'schema1'
        structure_data = {
            "constraints": [
                {
                    "constraint_type": "PRIMARY KEY",
                    "constraint_parameter": "id",
                    "reference_table": None,
                    "reference_column": None
                }
            ],
            "columns": [
                {
                    "name": "id",
                    "data_type": "integer",
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

        c_basic_resp = self.__class__.client.put(
            '/api/v0/schema/{schema}/tables/{table}/'.format(
                schema=self.test_schema, table=self.test_table),
            data=json.dumps({'query': structure_data}),
            HTTP_AUTHORIZATION='Token %s' % self.__class__.token,
            content_type='application/json')

        assert c_basic_resp.status_code==201, c_basic_resp.json().get('reason','No reason returned')

    def tearDown(self):
        meta_schema = actions.get_meta_schema_name(self.test_schema)
        if actions.has_table(
                dict(table=self.test_table, schema=self.test_schema)):
            actions.perform_sql(
                "DROP TABLE IF EXISTS {schema}.{table} CASCADE".format(
                    schema=meta_schema,
                    table=actions.get_insert_table_name(self.test_schema,
                                                        self.test_table)
                ))
            actions.perform_sql(
                "DROP TABLE IF EXISTS {schema}.{table} CASCADE".format(
                    schema=meta_schema,
                    table=actions.get_edit_table_name(self.test_schema,
                                                      self.test_table)
                ))
            actions.perform_sql(
                "DROP TABLE IF EXISTS {schema}.{table} CASCADE".format(
                    schema=meta_schema,
                    table=actions.get_delete_table_name(self.test_schema,
                                                        self.test_table)
                ))
            actions.perform_sql(
                "DROP TABLE IF EXISTS {schema}.{table} CASCADE".format(
                    schema=self.test_schema,
                    table=self.test_table
                ))

    def test_put_with_id(self):
        row = {'id': 1, 'name': 'John Doe', 'address': None}
        response = self.__class__.client.put(
            '/api/v0/schema/{schema}/tables/{table}/rows/1'.format(
                schema=self.test_schema, table=self.test_table),
            data=json.dumps({'query': row}),
            HTTP_AUTHORIZATION='Token %s' % self.__class__.token,
            content_type='application/json')

        self.assertEqual(response.status_code, 201, response.json().get('reason', 'No reason returned'))

        response = self.__class__.client.get(
            '/api/v0/schema/{schema}/tables/{table}/rows/1'.format(
                schema=self.test_schema, table=self.test_table))

        self.assertEqual(response.status_code, 200,
                         response.json().get('reason', 'No reason returned'))

        self.assertDictEqualKeywise(response.json(), row)

    def test_put_with_wrong_id(self):
        response = self.__class__.client.put(
            '/api/v0/schema/{schema}/tables/{table}/rows/1'.format(
                schema=self.test_schema, table=self.test_table),
            data=json.dumps({'query': {'id': 2, 'name': 'John Doe',
                                       'address': None}}),
            HTTP_AUTHORIZATION='Token %s' % self.__class__.token,
            content_type='application/json')

        self.assertEqual(response.status_code, 409, response.json().get('reason', 'No reason returned'))

    def test_put_with_existing_id(self):
        self.test_put_with_id()

        another_row = {'id': 1, 'name': 'Mary Doe', 'address': "Mary's Street"}

        response = self.__class__.client.put(
            '/api/v0/schema/{schema}/tables/{table}/rows/1'.format(
                schema=self.test_schema, table=self.test_table),
            data=json.dumps({'query': another_row}),
            HTTP_AUTHORIZATION='Token %s' % self.__class__.token,
            content_type='application/json')

        self.assertEqual(response.status_code, 200, response.json().get('reason', 'No reason returned'))

        response = self.__class__.client.get(
            '/api/v0/schema/{schema}/tables/{table}/rows/1'.format(
                schema=self.test_schema, table=self.test_table))

        self.assertEqual(response.status_code, 200,
                         response.json().get('reason', 'No reason returned'))

        self.assertDictEqualKeywise(response.json(), another_row)
