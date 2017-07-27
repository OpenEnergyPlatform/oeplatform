How to work with the API - An example
=====================================

.. testsetup::

    from api.actions import _get_engine
    engine = _get_engine()
    connection = engine.connect()
    connection.execute('CREATE SCHEMA IF NOT EXISTS example_schema;')
    connection.execute('CREATE SCHEMA IF NOT EXISTS _example_schema;')
    connection.close()

    oep_url = 'http://localhost:8000'
    from oeplatform.securitysettings import token_test_user as your_token


Authenticate
************

The OpenEnergy Platform API uses token authentication. Each user has a unique
token assigned to it that will be used as an authentication password. You can
access you token by visiting you profile on the OEP. In order to issue PUT or
POST request you have to include this token in the *Authorization*-field of
your request:

* Authorization: Token *your-token*


Create table
************

We want to create the following table with primary key `id`:

+-----------+-------------------+-----------------------+
| *id*: int | name: varchar(50) | geom: geometry(Point) |
+===========+===================+=======================+
|           |                   |                       |
+-----------+-------------------+-----------------------+

In order to do so, we send the following PUT request::

    PUT oep.iks.cs.ovgu.de/api/v0/schema/example_schema/tables/example_table/
    {
        "query": {
            "columns": [
                {
                    "name":"id",
                    "data_type": "Integer",
                    "is_nullable": "NO"
                },{
                    "name":"name",
                    "data_type": "varchar",
                    "character_maximum_length": "50"
                },{
                    "name":"geom",
                    "data_type": "geometry(point)"
                }
            ],
            "constraints": [
                {
                    "constraint_type": "PRIMARY KEY",
                    "constraint_parameter": "id",
                }
            ]
        }
    }

and include the following headers:

* Content-Type: application/json
* Authorization: Token *your-token*

You can use any tool that can send HTTP-requests. E.g. you could use the linux
tool **curl**::

    curl
        -X PUT
        -H 'Content-Type: application/json'
        -H 'Authorization: Token <your-token>'
        -d '{
                "query": {
                    "columns": [
                        {
                            "name":"id",
                            "data_type": "Integer",
                            "is_nullable": "NO"
                        },{
                            "name":"name",
                            "data_type": "varchar",
                            "character_maximum_length": "50"
                        },{
                            "name":"geom",
                            "data_type": "geometry(point)"
                        }
                    ],
                    "constraints": [
                        {
                            "constraint_type": "PRIMARY KEY",
                            "constraint_parameter": "id",
                        }
                    ]
                }
            }'
        oep.iks.cs.ovgu.de/api/v0/schema/example_schema/tables/example_table/


or **python**:

.. doctest::

    >>> import requests
    >>> data = { "query": { "columns": [ { "name":"id", "data_type": "serial", "is_nullable": "NO" },{ "name":"name", "data_type": "varchar", "character_maximum_length": "50" },{ "name":"geom", "data_type": "geometry(point)" } ], "constraints": [ { "constraint_type": "PRIMARY KEY", "constraint_parameter": "id" } ] } }
    >>> requests.put(oep_url+'/api/v0/schema/example_schema/tables/example_table/', json=data, headers={'Authorization': 'Token %s'%your_token} )
    <Response [201]>

If everything went right, you will receive a 201-Resonse_ and the table has
been created.

.. doctest::

    >>> result = requests.get(oep_url+'/api/v0/schema/example_schema/tables/example_table/columns')
    >>> result.status_code
    200
    >>> json_result = result.json()
    >>> json_result['id'] == {'character_maximum_length': None, 'maximum_cardinality': None, 'is_nullable': 'NO', 'data_type': 'integer', 'numeric_precision': 32, 'character_octet_length': None, 'interval_type': None, 'dtd_identifier': '1', 'interval_precision': None, 'numeric_scale': 0, 'is_updatable': 'YES', 'datetime_precision': None, 'ordinal_position': 1, 'column_default': "nextval('example_schema.example_table_id_seq'::regclass)", 'numeric_precision_radix': 2}
    True
    >>> json_result['geom'] == {'character_maximum_length': None, 'maximum_cardinality': None, 'is_nullable': 'YES', 'data_type': 'USER-DEFINED', 'numeric_precision': None, 'character_octet_length': None, 'interval_type': None, 'dtd_identifier': '3', 'interval_precision': None, 'numeric_scale': None, 'is_updatable': 'YES', 'datetime_precision': None, 'ordinal_position': 3, 'column_default': None, 'numeric_precision_radix': None}
    True
    >>> json_result['name'] == {'character_maximum_length': 50, 'maximum_cardinality': None, 'is_nullable': 'YES', 'data_type': 'character varying', 'numeric_precision': None, 'character_octet_length': 200, 'interval_type': None, 'dtd_identifier': '2', 'interval_precision': None, 'numeric_scale': None, 'is_updatable': 'YES', 'datetime_precision': None, 'ordinal_position': 2, 'column_default': None, 'numeric_precision_radix': None}
    True


.. _200-Resonse: https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
.. _201-Resonse: https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html

Insert data
***********

You can insert data into a specific table by sending a request to its
`/rows` subresource. The `query` part of the sent data contians the row you want
to insert in form of a JSON-dictionary:::

    {
        'name_of_column_1': 'value_in_column_1',
        'name_of_column_2': 'value_in_column_2',
        ...
    }

If you the row you want to insert should have a specific id, send a PUT-request
to the `/rows/{id}/` subresource.
In case the id should be generated automatically, just ommit the id field in the
data dictionary and send a POST-request to the `/rows/new` subresource. If
successful, the response will contain the id of the new row.

In the following example, we want to add a row containing just the name
"John Doe", **but** we do not want to set the the id of this entry.

**curl**::

    curl
        -X POST
        -H "Content-Type: application/json"
        -H 'Authorization: Token <your-token>'
        -d '{"query": {"name": "John Doe"}}'
        oep.iks.cs.ovgu.de/api/v0/schema/example_schema/tables/example_table/rows/

**python**:

.. doctest::

    >>> import requests
    >>> data = {"query": {"name": "John Doe"}}
    >>> result = requests.post(oep_url+'/api/v0/schema/example_schema/tables/example_table/rows/new', json=data, headers={'Authorization': 'Token %s'%your_token} )
    >>> result.status_code
    201
    >>> json_result = result.json()
    >>> json_result['data'] # Show the id of the new row
    [[1]]

Alternatively, we can specify that the new row should be stored under id 12:

**python**:

.. doctest::

    >>> import requests
    >>> data = {"query": {"name": "Mary Doe XII"}}
    >>> result = requests.put(oep_url+'/api/v0/schema/example_schema/tables/example_table/rows/12', json=data, headers={'Authorization': 'Token %s'%your_token} )
    >>> result.status_code
    201

Our database should have the following structure now:

+-----------+-------------------+-----------------------+
| *id*: int | name: varchar(50) | geom: geometry(Point) |
+===========+===================+=======================+
|       1   | John Doe          | NULL                  |
+-----------+-------------------+-----------------------+
|       12  | Mary Doe XII      | NULL                  |
+-----------+-------------------+-----------------------+

Select data
***********

You can insert data into a specific table by sending a GET-request to its
`/rows` subresource.
No authorization is required to do so.

**curl**::

    curl
        -X GET
        oep.iks.cs.ovgu.de/api/v0/schema/example_schema/tables/example_table/rows/

The data will be returned as list of JSON-dictionaries similar to the ones used
when adding new rows::

    [
        {
            "name": "John Doe",
            "geom": null,
            "id": 1
        }
    ]

**python**:

.. doctest::

    >>> result = requests.get(oep_url+'/api/v0/schema/example_schema/tables/example_table/rows/', )
    >>> result.status_code
    200
    >>> json_result = result.json()
    >>> json_result ==  [{'id': 1, 'name': 'John Doe', 'geom': None}, {'id': 12, 'name': 'Mary Doe XII', 'geom': None}]
    True


There are also optional parameters for these GET-queries:

* limit: Limit the number of returned rows
* offset: Ignore the specified amount of rows
* orderby: Name of a column to refer when ordering
* column: Name of a column to include in the results. If not present, all
          columns are returned
* where: Constraint fourmulated as `VALUE+OPERATOR+VALUE` with

    * VALUE: Constant or name of a column
    * OPERATOR: One of the following:

        * `EQUALS` or `=`,
        * `GREATER` or `>`,
        * `LOWER` or `<`,
        * `NOTEQUAL` or `!=` or `<>`,
        * `NOTGREATER` or `<=`,
        * `NOTLOWER` or `>=`,

.. doctest::

    >>> result = requests.get(oep_url+"/api/v0/schema/example_schema/tables/example_table/rows/?where=name=John+Doe", )
    >>> result.status_code
    200
    >>> json_result = result.json()
    >>> json_result == [{'id': 1, 'name': 'John Doe', 'geom': None}]
    True

.. doctest::

    >>> result = requests.get(oep_url+"/api/v0/schema/example_schema/tables/example_table/rows/1", )
    >>> result.status_code
    200
    >>> json_result = result.json()
    >>> json_result == {'id': 1, 'name': 'John Doe', 'geom': None}
    True

.. doctest::

    >>> result = requests.get(oep_url+"/api/v0/schema/example_schema/tables/example_table/rows/?offset=1")
    >>> result.status_code
    200
    >>> json_result = result.json()
    >>> json_result == [{'id': 12, 'name': 'Mary Doe XII', 'geom': None}]
    True

.. doctest::

    >>> result = requests.get(oep_url+"/api/v0/schema/example_schema/tables/example_table/rows/?column=name&column=id")
    >>> result.status_code
    200
    >>> json_result = result.json()
    >>> json_result == [{'id': 1, 'name': 'John Doe'},{'id': 12, 'name': 'Mary Doe XII'}]
    True

Add columns table
*****************

.. doctest::

    >>> data = {'data_type': 'varchar', 'character_maximum_length': 30}
    >>> result = requests.put(oep_url+"/api/v0/schema/example_schema/tables/example_table/columns/first_name", json=data, headers={'Authorization': 'Token %s'%your_token})
    >>> result.status_code
    201

.. doctest::

    >>> result = requests.get(oep_url+"/api/v0/schema/example_schema/tables/example_table/columns/first_name")
    >>> result.status_code
    200
    >>> result.json() == {'numeric_scale': None, 'numeric_precision_radix': None, 'is_updatable': 'YES', 'maximum_cardinality': None, 'character_maximum_length': 30, 'character_octet_length': 120, 'ordinal_position': 4, 'is_nullable': 'YES', 'interval_type': None, 'data_type': 'character varying', 'dtd_identifier': '4', 'column_default': None, 'datetime_precision': None, 'interval_precision': None, 'numeric_precision': None}
    True

Alter data
**********

Our current table looks as follows:

+-----------+-------------------+-----------------------+------------------------+
| *id*: int | name: varchar(50) | geom: geometry(Point) | first_name: varchar(30)|
+===========+===================+=======================+========================+
|       1   | John Doe          | NULL                  | NULL                   |
+-----------+-------------------+-----------------------+------------------------+
|       12  | Mary Doe XII      | NULL                  | NULL                   |
+-----------+-------------------+-----------------------+------------------------+

Our next task is to distribute for and last name to the different columns:

.. doctest::

    >>> result = requests.get(oep_url+'/api/v0/schema/example_schema/tables/example_table/rows/') # Load the names via GET
    >>> result.status_code
    200
    >>> for row in result.json():
    ...     first_name, last_name = str(row['name']).split(' ', 1) # Split the names at the first space
    ...     data = {'query': {'name': last_name, 'first_name': first_name}} # Build the data dictionary and post it to /rows/<id>
    ...     result = requests.post(oep_url+'/api/v0/schema/example_schema/tables/example_table/rows/{id}'.format(id=row['id']), json=data, headers={'Authorization': 'Token %s'%your_token})
    ...     result.status_code
    200
    200

Now, our table looks as follows:

+-----------+-------------------+-----------------------+------------------------+
| *id*: int | name: varchar(50) | geom: geometry(Point) | first_name: varchar(30)|
+===========+===================+=======================+========================+
|       1   | Doe               | NULL                  | John                   |
+-----------+-------------------+-----------------------+------------------------+
|       12  | Doe XII           | NULL                  | Mary                   |
+-----------+-------------------+-----------------------+------------------------+

Alter tables
************

Currently, rows are allowed that contain no first name. In order to prohibit
such behaviour, we have to set column `first_name` to `NOT NULL`. Such `ALTER
TABLE` commands can be executed by POST-ing a dictionary with the corresponding
values to the column's resource:

.. doctest::

    >>> data = {'is_nullable': 'NO'}
    >>> result = requests.post(oep_url+"/api/v0/schema/example_schema/tables/example_table/columns/first_name", json=data, headers={'Authorization': 'Token %s'%your_token} )
    >>> result.status_code
    200

We can check, whether your command worked by retrieving the corresponding resource:

.. doctest::

    >>> result = requests.get(oep_url+"/api/v0/schema/example_schema/tables/example_table/columns/first_name")
    >>> result.status_code
    200
    >>> json_result = result.json()
    >>> json_result['is_nullable']
    'NO'

After prohibiting null-values in the first name column, such rows can not be
added anymore.

.. doctest::

    >>> import requests
    >>> data = {"query": {"name": "McPaul"}}
    >>> result = requests.post(oep_url+'/api/v0/schema/example_schema/tables/example_table/rows/new', json=data, headers={'Authorization': 'Token %s'%your_token} )
    >>> result.status_code
    500
    >>> result.json()['reason']
    'ERROR:  null value in column "first_name" violates not-null constraint'

.. doctest::

    >>> import requests
    >>> data = {"query": {"name": "McPaul"}}
    >>> result = requests.delete(oep_url+'/api/v0/schema/example_schema/tables/example_table/rows/1', json=data, headers={'Authorization': 'Token %s'%your_token} )
    >>> result.status_code
    200

.. testcleanup::

    from api.actions import _get_engine
    engine = _get_engine()
    connection = engine.connect()
    connection.execute('DROP SCHEMA example_schema CASCADE;')
    connection.execute('DROP SCHEMA _example_schema CASCADE;')
    connection.close()
