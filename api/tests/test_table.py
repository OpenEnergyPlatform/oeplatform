import json

from api.tests import APITestCase

_TYPES = ['bigint', 'bit', 'boolean', 'char', 'date', 'decimal', 'float',
          'integer', 'interval', 'json', 'nchar', 'numeric', 'real', 'smallint',
          'timestamp', 'text', 'time', 'varchar', 'character varying']


_TYPEMAP = {
    'char': 'character',
    'decimal': 'numeric',
    'float': 'double precision',
    'int': 'integer',
    'nchar': 'character',
    'timestamp': 'timestamp without time zone',
    'time': 'time without time zone',
    'varchar': 'character varying',
    'character varying': 'character varying'
}


class TestPut(APITestCase):

    def checkStructure(self):
        response = self.__class__.client.get(
            '/api/v0/schema/{schema}/tables/{table}/'.format(schema=self.test_schema, table=self.test_table))
        body = response.json()

        self.assertEqual(body['schema'], self.test_schema, "Schema does not match.")
        self.assertEqual(body['name'], self.test_table, "Table does not match.")

        for column in self._structure_data['columns']:
            for key in column:
                # name is a programmer-introduced key.
                # We are able to use a list instead of a dictonary to get better iteration possibilities.
                if key != 'name':
                    value = column[key]
                    covalue = body['columns'][column['name']][key]
                    if key == 'data_type':
                        value = _TYPEMAP.get(value, value)

                    self.assertEqual(value, covalue,
                                     "Key '{key}' does not match.".format(key=key))

        self.assertEqual(response.status_code, 200, "Status Code is not 200.")

    def test_create_table(self):
        self._structure_data = {
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
                           }, {
                    "name": "col_varchar123",
                    "data_type": 'character varying',
                    "is_nullable": True,
                    "character_maximum_length": 123
                }, {
                    "name": "col_intarr",
                    "data_type": 'integer[]',
                    "is_nullable": True,
                }
                       ] + [
                           {
                               "name": "col_{type}_{null}".format(
                                   type=ctype.lower().replace(' ', '_'),
                                   null='true' if null else 'false'),
                               "data_type": ctype.lower(),
                               "is_nullable": null,
                           } for ctype in _TYPES for null in [True, False]]
        }
        self.test_table = 'table_all_columns'
        c_basic_resp = self.__class__.client.put(
            '/api/v0/schema/{schema}/tables/{table}/'.format(schema=self.test_schema, table=self.test_table),
            data=json.dumps({'query': self._structure_data}),
            HTTP_AUTHORIZATION='Token %s' % self.__class__.token,
            content_type='application/json')

        self.assertEqual(c_basic_resp.status_code, 201, c_basic_resp.json().get('reason', 'No reason returned'))
        self.checkStructure()

    def test_create_table_defaults(self):
        self._structure_data = {
            "constraints": [
                {
                    "constraint_type": "PRIMARY KEY",
                    "constraint_parameter": "id",
                }
            ],
            "columns": [
                {
                    "name": "id",
                    "data_type": "integer",
                }, {
                    "name": "id2",
                    "data_type": "integer",
                }, {
                    "name": "text",
                    "data_type": "varchar",
                }
            ]
        }
        self.test_table = 'table_defaults'
        response = self.__class__.client.put(
            '/api/v0/schema/{schema}/tables/{table}/'.format(
                schema=self.test_schema, table=self.test_table),
            data=json.dumps({'query': self._structure_data}),
            HTTP_AUTHORIZATION='Token %s' % self.__class__.token,
            content_type='application/json')

        self.assertEqual(response.status_code, 201,
                         response.json().get('reason',
                                             'No reason returned'))

        response = self.__class__.client.get(
            '/api/v0/schema/{schema}/tables/{table}/'.format(
                schema=self.test_schema, table=self.test_table))
        body = response.json()

        self.assertEqual(body['schema'], self.test_schema,
                         "Schema does not match.")
        self.assertEqual(body['name'], self.test_table, "Table does not match.")

        self.assertDictEqualKeywise(body['columns']['id'],{
            'character_maximum_length': None,
            'character_octet_length': None,
            'column_default': None,
            'data_type': 'integer',
            'datetime_precision': None,
            'dtd_identifier': '1',
            'interval_precision': None,
            'interval_type': None,
            'is_nullable': False,
            'is_updatable': True,
            'maximum_cardinality': None,
            'numeric_precision': 32,
            'numeric_precision_radix': 2,
            'numeric_scale': 0,
        },['ordinal_position'])
        self.assertDictEqualKeywise(body['columns']['id2'],{
            'character_maximum_length': None,
            'character_octet_length': None,
            'column_default': None,
            'data_type': 'integer',
            'datetime_precision': None,
            'dtd_identifier': '2',
            'interval_precision': None,
            'interval_type': None,
            'is_nullable': True,
            'is_updatable': True,
            'maximum_cardinality': None,
            'numeric_precision': 32,
            'numeric_precision_radix': 2,
            'numeric_scale': 0,
        },['ordinal_position'])
        self.assertDictEqualKeywise(body['columns']['text'],{
            'character_maximum_length': None,
            'character_octet_length': 1073741824,
            'column_default': None,
            'data_type': 'character varying',
            'datetime_precision': None,
            'dtd_identifier': '3',
            'interval_precision': None,
            'interval_type': None,
            'is_nullable': True,
            'is_updatable': True,
            'maximum_cardinality': None,
            'numeric_precision': None,
            'numeric_precision_radix': None,
            'numeric_scale': None,
        },['ordinal_position'])

    def test_create_table_anonymous(self):
        self._structure_data = {
            "constraints": [
                {
                    "constraint_type": "PRIMARY KEY",
                    "constraint_parameter": "id",
                }
            ],
            "columns": [
                {
                    "name": "id",
                    "data_type": "integer",
                }
            ]
        }

        self.test_table = 'table_anonymous'
        response = self.__class__.client.put(
            '/api/v0/schema/{schema}/tables/{table}/'.format(
                schema=self.test_schema, table=self.test_table),
            data=json.dumps({'query': self._structure_data}),
            content_type='application/json')

        self.assertEqual(response.status_code, 403)

        response = self.__class__.client.get(
            '/api/v0/schema/{schema}/tables/{table}/'.format(
                schema=self.test_schema, table=self.test_table))

        self.assertEqual(response.status_code, 404, response.json())

    def test_anonymous(self):
        self._structure_data = {
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
                           }, {
                    "name": "col_varchar123",
                    "data_type": 'character varying',
                    "is_nullable": True,
                    "character_maximum_length": 123
                }, {
                    "name": "col_intarr",
                    "data_type": 'integer[]',
                    "is_nullable": True,
                }
                       ] + [
                           {
                               "name": "col_{type}_{null}".format(
                                   type=ctype.lower().replace(' ', '_'),
                                   null='true' if null else 'false'),
                               "data_type": ctype.lower(),
                               "is_nullable": null,
                           } for ctype in _TYPES for null in [True, False]]
        }
        self.test_table = 'table_all_columns'
        c_basic_resp = self.__class__.client.put(
            '/api/v0/schema/{schema}/tables/{table}/'.format(schema=self.test_schema, table=self.test_table),
            data=json.dumps({'query': self._structure_data}),
            content_type='application/json')

        self.assertEqual(c_basic_resp.status_code, 403, c_basic_resp.json().get('reason', 'No reason returned'))