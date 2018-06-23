from . import APITestCase
from .util import load_content, load_content_as_json, content2json
from api import actions
import json

from shapely import wkt, wkb

class TestPut(APITestCase):

    def setUp(self):
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
                }, {
                    "name": "geom",
                    "data_type": "Geometry (Point)",
                    "is_nullable": True,
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
        row['geom'] = None
        response = self.__class__.client.get(
            '/api/v0/schema/{schema}/tables/{table}/rows/1'.format(
                schema=self.test_schema, table=self.test_table))

        self.assertEqual(response.status_code, 200,
                         response.json())

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

        another_row['geom'] = None

        self.assertDictEqualKeywise(response.json(), another_row)

    def test_put_geometry(self):
        row = {'id': 1, 'name': 'Mary Doe', 'address': "Mary's Street", 'geom': 'POINT(-71.160281 42.258729)'}

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

        row['geom'] = wkb.dumps(wkt.loads(row['geom']), hex=True)
        self.assertDictEqualKeywise(response.json(), row)

    def test_put_geometry_wtb(self):
        row = {'id': 1, 'name': 'Mary Doe', 'address': "Mary's Street",
               'geom':  wkb.dumps(wkt.loads('POINT(-71.160281 42.258729)'), hex=True)}

        response = self.__class__.client.put(
            '/api/v0/schema/{schema}/tables/{table}/rows/1'.format(
                schema=self.test_schema, table=self.test_table),
            data=json.dumps({'query': row}),
            HTTP_AUTHORIZATION='Token %s' % self.__class__.token,
            content_type='application/json')

        self.assertEqual(response.status_code, 201,
                         response.json().get('reason',
                                             'No reason returned'))

        response = self.__class__.client.get(
            '/api/v0/schema/{schema}/tables/{table}/rows/1'.format(
                schema=self.test_schema, table=self.test_table))

        self.assertEqual(response.status_code, 200,
                         response.json().get('reason',
                                             'No reason returned'))

        self.assertDictEqualKeywise(response.json(), row)

    def test_anonymous(self):
        row = {'id': 1, 'name': 'John Doe', 'address': None}
        response = self.__class__.client.put(
            '/api/v0/schema/{schema}/tables/{table}/rows/1'.format(
                schema=self.test_schema, table=self.test_table),
            data=json.dumps({'query': row}),
            content_type='application/json')

        self.assertEqual(response.status_code, 403, response.json())

    def test_wrong_user(self):
        row = {'id': 1, 'name': 'John Doe', 'address': None}
        response = self.__class__.client.put(
            '/api/v0/schema/{schema}/tables/{table}/rows/1'.format(
                schema=self.test_schema, table=self.test_table),
            data=json.dumps({'query': row}),
            HTTP_AUTHORIZATION='Token %s' % self.__class__.other_token,
            content_type='application/json')

        self.assertEqual(response.status_code, 403, response.json())


class TestPost(APITestCase):
    def setUp(self):
        self.rows = [{'id': 1, 'name': 'John Doe', 'address': None, 'geom': 'Point(-71.160281 42.258729)'}]
        self.test_table = 'test_table_rows'
        self.test_schema = 'test'
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
                }, {
                    "name": "geom",
                    "data_type": "geometry (point)",
                    "is_nullable": True,
                }
            ]
        }

        c_basic_resp = self.__class__.client.put(
            '/api/v0/schema/{schema}/tables/{table}/'.format(
                schema=self.test_schema, table=self.test_table),
            data=json.dumps({'query': structure_data}),
            HTTP_AUTHORIZATION='Token %s' % self.__class__.token,
            content_type='application/json')

        assert c_basic_resp.status_code==201, 'Returned %d: %s'%(c_basic_resp.status_code, c_basic_resp.json().get('reason','No reason returned'))

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

    def test_simple_post_new(self, rid=1):
        row = {'id': rid, 'name': 'Mary Doe', 'address': "Mary's Street",
               'geom':'POINT(-71.160281 42.258729)'}

        response = self.__class__.client.post(
            '/api/v0/schema/{schema}/tables/{table}/rows/new'.format(
                schema=self.test_schema, table=self.test_table),
            data=json.dumps({'query': row}),
            HTTP_AUTHORIZATION='Token %s' % self.__class__.token,
            content_type='application/json')

        self.assertEqual(response.status_code, 201,
                         load_content_as_json(response).get('reason', 'No reason returned'))

        response = self.__class__.client.get(
            '/api/v0/schema/{schema}/tables/{table}/rows/{rid}'.format(
                schema=self.test_schema, table=self.test_table, rid=rid))

        self.assertEqual(response.status_code, 200,
                         response.json().get('reason', 'No reason returned'))

        row['geom'] = wkb.dumps(wkt.loads(row['geom']), hex=True)
        self.assertDictEqualKeywise(response.json(), row)

    def test_anonymous(self, rid=1):
        row = {'id': rid, 'name': 'Mary Doe', 'address': "Mary's Street",
               'geom':'POINT(-71.160281 42.258729)'}

        response = self.__class__.client.post(
            '/api/v0/schema/{schema}/tables/{table}/rows/new'.format(
                schema=self.test_schema, table=self.test_table),
            data=json.dumps({'query': row}),
            content_type='application/json')

        self.assertEqual(response.status_code, 403,
                         response.json().get('reason', 'No reason returned'))

    def test_wrong_user(self, rid=1):
        row = {'id': rid, 'name': 'Mary Doe', 'address': "Mary's Street",
               'geom':'POINT(-71.160281 42.258729)'}

        response = self.__class__.client.post(
            '/api/v0/schema/{schema}/tables/{table}/rows/new'.format(
                schema=self.test_schema, table=self.test_table),
            data=json.dumps({'query': row}),
            HTTP_AUTHORIZATION='Token %s' % self.__class__.other_token,
            content_type='application/json')

        self.assertEqual(response.status_code, 403,
                         response.json().get('reason', 'No reason returned'))

    def test_simple_post_existing(self):
        self.test_simple_post_new()
        self.test_simple_post_new(rid=2)
        row = {'id': 2, 'name': 'John Doe', 'address': "John's Street",
               'geom':'POINT(42.258729 -71.160281)'}

        self.check_api_post(
            '/api/v0/schema/{schema}/tables/{table}/rows/2'.format(
                schema=self.test_schema, table=self.test_table),
            data={'query': row}
        )

        row['geom'] = wkb.dumps(wkt.loads(row['geom']), hex=True)

        self.check_api_get('/api/v0/schema/{schema}/tables/{table}/rows/2'.format(
                schema=self.test_schema, table=self.test_table), expected_result=row)

        # Check whether other rows remained unchanged
        row = {'id': 1, 'name': 'Mary Doe', 'address': "Mary's Street",
               'geom': 'POINT(-71.160281 42.258729)'}
        row['geom'] = wkb.dumps(wkt.loads(row['geom']), hex=True)
        self.check_api_get(
            '/api/v0/schema/{schema}/tables/{table}/rows/1'.format(
                schema=self.test_schema, table=self.test_table),
            expected_result=row)

    def test_bulk_insert(self):
        rows = [{'id': rid, 'name': 'Mary Doe', 'address': "Mary's Street",
               'geom': None} for rid in range(0,23)]

        response = self.__class__.client.post(
            '/api/v0/schema/{schema}/tables/{table}/rows/new'.format(
                schema=self.test_schema, table=self.test_table),
            data=json.dumps({'query': rows}),
            HTTP_AUTHORIZATION='Token %s' % self.__class__.token,
            content_type='application/json')

        self.assertEqual(response.status_code, 201,
                         load_content_as_json(response).get('reason', 'No reason returned'))

        response = self.__class__.client.get(
            '/api/v0/schema/{schema}/tables/{table}/rows/'.format(
                schema=self.test_schema, table=self.test_table))

        content = load_content(response)

        self.assertEqual(response.status_code, 200,
                         'Returned %d: %s'%(response.status_code, content))

        content = content2json(content)
        self.assertListEqual(content, rows)

class TestGet(APITestCase):
    @classmethod
    def setUpClass(cls):
        super(TestGet, cls).setUpClass()
        cls.rows = [{'id': 1, 'name': 'John Doe', 'address': None, 'geom': 'Point(-71.160281 42.258729)'}]
        cls.test_table = 'test_table_rows'
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
                }, {
                    "name": "geom",
                    "data_type": "geometry (point)",
                    "is_nullable": True,
                }
            ]
        }

        c_basic_resp = cls.client.put(
            '/api/v0/schema/{schema}/tables/{table}/'.format(
                schema=cls.test_schema, table=cls.test_table),
            data=json.dumps({'query': structure_data}),
            HTTP_AUTHORIZATION='Token %s' % cls.token,
            content_type='application/json')

        assert c_basic_resp.status_code==201, c_basic_resp.json()


        cls.rows = [{'id': i, 'name': 'Mary Doe', 'address': "Mary's Street",
               'geom': '0101000000E44A3D0B42CA51C06EC328081E214540'} for i in range(100)]

        response = cls.client.post(
            '/api/v0/schema/{schema}/tables/{table}/rows/new'.format(
                schema=cls.test_schema, table=cls.test_table),
            data=json.dumps({'query': cls.rows}),
            HTTP_AUTHORIZATION='Token %s' % cls.token,
            content_type='application/json')

        assert response.status_code == 201, response.json().get(
            'reason', 'No reason returned')

    @classmethod
    def tearDownClass(self):
        super(TestGet, self).tearDownClass()
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

    def test_simple_get(self):
        response = self.__class__.client.get(
            '/api/v0/schema/{schema}/tables/{table}/rows/'.format(
                schema=self.test_schema, table=self.test_table))

        content = load_content_as_json(response)

        self.assertEqual(response.status_code, 200, content)

        for c in zip(content, self.rows):
            self.assertDictEqualKeywise(*c)

    def test_simple_offset(self):
        response = self.__class__.client.get(
            '/api/v0/schema/{schema}/tables/{table}/rows/?offset=50'.format(
                schema=self.test_schema, table=self.test_table))

        content = load_content_as_json(response)

        self.assertEqual(response.status_code, 200, content)

        for c in zip(content, self.rows[50:]):
            self.assertDictEqualKeywise(*c)

    def test_simple_limit(self):
        response = self.__class__.client.get(
            '/api/v0/schema/{schema}/tables/{table}/rows/?limit=50'.format(
                schema=self.test_schema, table=self.test_table))

        self.assertEqual(response.status_code, 200,
                         load_content_as_json(response))

    def test_simple_where_geq(self):
        response = self.__class__.client.get(
            '/api/v0/schema/{schema}/tables/{table}/rows/?where=id>=50'.format(
                schema=self.test_schema, table=self.test_table))
        content = load_content_as_json(response)
        self.assertEqual(response.status_code, 200, content)
        for c in zip(content, [row for row in self.rows if row['id']>=50]):
            self.assertDictEqualKeywise(*c)


    def test_simple_order_by(self):
        response = self.__class__.client.get(
            '/api/v0/schema/{schema}/tables/{table}/rows/?orderby=id'.format(
                schema=self.test_schema, table=self.test_table))

        content = load_content(response)
        self.assertEqual(response.status_code, 200, content)

        content = content2json(content)
        for c in zip(content, sorted([row for row in self.rows], key=lambda x: x['id'])):
            self.assertDictEqualKeywise(*c)

class TestDelete(APITestCase):
    @classmethod
    def setUpClass(cls):
        super(TestDelete, cls).setUpClass()
        cls.rows = [{'id': 1, 'name': 'John Doe', 'address': None, 'geom': 'Point(-71.160281 42.258729)'}]
        cls.test_table = 'test_table_rows'
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
                }, {
                    "name": "geom",
                    "data_type": "geometry (point)",
                    "is_nullable": True,
                }
            ]
        }

        c_basic_resp = cls.client.put(
            '/api/v0/schema/{schema}/tables/{table}/'.format(
                schema=cls.test_schema, table=cls.test_table),
            data=json.dumps({'query': structure_data}),
            HTTP_AUTHORIZATION='Token %s' % cls.token,
            content_type='application/json')

        assert c_basic_resp.status_code==201, c_basic_resp.json()


        cls.rows = [{'id': i, 'name': 'Mary Doe', 'address': "Mary's Street",
               'geom': '0101000000E44A3D0B42CA51C06EC328081E214540'} for i in range(100)]

        response = cls.client.post(
            '/api/v0/schema/{schema}/tables/{table}/rows/new'.format(
                schema=cls.test_schema, table=cls.test_table),
            data=json.dumps({'query': cls.rows}),
            HTTP_AUTHORIZATION='Token %s' % cls.token,
            content_type='application/json')

        assert response.status_code == 201, response.json().get(
            'reason', 'No reason returned')

    @classmethod
    def tearDownClass(self):
        super(TestDelete, self).tearDownClass()
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

    def test_simple(self):
        row = self.rows.pop()
        response = self.__class__.client.delete(
            '/api/v0/schema/{schema}/tables/{table}/rows/{rid}'.format(
                schema=self.test_schema, table=self.test_table, rid=row['id']),
            HTTP_AUTHORIZATION='Token %s' % self.__class__.token,
            content_type='application/json')
        self.assertEqual(response.status_code, 200,
                         response.json())

        response = self.__class__.client.get(
            '/api/v0/schema/{schema}/tables/{table}/rows/{rid}'.format(
                schema=self.test_schema, table=self.test_table, rid=row['id']),
            content_type='application/json')
        self.assertEqual(response.status_code, 404,
                         response.json())

        self.check_api_get('/api/v0/schema/{schema}/tables/{table}/rows/'.format(
                schema=self.test_schema, table=self.test_table),
            expected_result=self.rows
        )

    def test_where(self):
        row = self.rows[10]
        deleted = [r for r in self.rows if r['id']<=row['id']]
        self.rows = [r for r in self.rows if r['id']>row['id']]
        response = self.__class__.client.delete(
            '/api/v0/schema/{schema}/tables/{table}/rows/?where=id<={rid}'.format(
                schema=self.test_schema, table=self.test_table, rid=row['id']),
            HTTP_AUTHORIZATION='Token %s' % self.__class__.token,
            content_type='application/json')
        self.assertEqual(response.status_code, 200,
                         response.json())
        for row in deleted:
            response = self.__class__.client.get(
                '/api/v0/schema/{schema}/tables/{table}/rows/{rid}'.format(
                    schema=self.test_schema, table=self.test_table, rid=row['id']),
                content_type='application/json')
            self.assertEqual(response.status_code, 404,
                             response.json())

        response = self.__class__.client.get(
            '/api/v0/schema/{schema}/tables/{table}/rows/'.format(
                schema=self.test_schema, table=self.test_table),
            content_type='application/json')

        content = load_content(response)
        self.assertEqual(response.status_code, 200, content)
        content = content2json(content)
        self.assertListEqual(content, self.rows)