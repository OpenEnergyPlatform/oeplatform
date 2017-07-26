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
                    "data_type": "Integer"
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
                            "data_type": "Integer"
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
    >>> data = { "query": { "columns": [ { "name":"id", "data_type": "serial" },{ "name":"name", "data_type": "varchar", "character_maximum_length": "50" },{ "name":"geom", "data_type": "geometry(point)" } ], "constraints": [ { "constraint_type": "PRIMARY KEY", "constraint_parameter": "id" } ] } }
    >>> requests.put(oep_url+'/api/v0/schema/example_schema/tables/example_table/', json=data, headers={'Authorization': 'Token %s'%your_token} )
    <Response [201]>


If everything went right, you will receive a 201-Resonse_ and the table has
been created.

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
data dictionary and send a POST-request to the `/rows/` subresource. If
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
    >>> result = requests.post(oep_url+'/api/v0/schema/example_schema/tables/example_table/rows/', json=data, headers={'Authorization': 'Token %s'%your_token} )
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

.. testcleanup::

    from api.actions import _get_engine
    engine = _get_engine()
    connection = engine.connect()
    connection.execute('DROP SCHEMA example_schema CASCADE;')
    connection.execute('DROP SCHEMA _example_schema CASCADE;')
    connection.close()
