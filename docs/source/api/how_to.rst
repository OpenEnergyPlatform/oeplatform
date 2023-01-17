*************************************
How to work with the API - An example
*************************************

.. testsetup::

    import os
    from oeplatform import securitysettings as sec
    oep_url = 'http://localhost:8000'
    your_token = os.environ.get("LOCAL_OEP_TOKEN")
    if your_token is None:
        if hasattr(sec, "token_test_user") and sec.token_test_user is not None:
            your_token = sec.token_test_user
        else:
            raise Exception("No token available, please set LOCAL_OEP_TOKEN or adapt your security settings")

.. note::

    The API is enable for the following schmemas only:

        * model_draft
        * sandbox


Authenticate
============

The OpenEnergy Platform API uses token authentication. Each user has a unique
token assigned to it that will be used as an authentication password. You can
access you token by visiting you profile on the OEP. In order to issue PUT or
POST request you have to include this token in the *Authorization*-field of
your request:

* Authorization: Token *your-token*


Create table
============

We want to create the following table with primary key `id`:

+-----------------+-------------------+-----------------------+
| *id*: bigserial | name: varchar(50) | geom: geometry(Point) |
+===========+===================+=======================+
|                 |                   |                       |
+-----------------+-------------------+-----------------------+

In order to do so, we send the following PUT request::

    PUT https://openenergy-platform.org/api/v0/schema/sandbox/tables/example_table/
    {
        "query": {
            "columns": [
                {
                    "name":"id",
                    "data_type": "Bigserial",
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
            ],
            "metadata": {"id": "sandbox.example_table"}
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
                            "data_type": "bigsersial",
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
                    ],
                    "metadata": {"id": "sandbox.example_table"}
                }
            }'
        https://openenergy-platform.org/api/v0/schema/sandbox/tables/example_table/


or **python**:

.. doctest::

    >>> import requests
    >>> data = { "query": { "columns": [ { "name":"id", "data_type": "bigserial", "is_nullable": "NO" },{ "name":"name", "data_type": "varchar", "character_maximum_length": "50" },{ "name":"geom", "data_type": "geometry(point)" } ], "constraints": [ { "constraint_type": "PRIMARY KEY", "constraint_parameter": "id" } ], "metadata": {"id": "sandbox.example_table"} } }
    >>> requests.put(oep_url+'/api/v0/schema/sandbox/tables/example_table/', json=data, headers={'Authorization': 'Token %s'%your_token} )
    <Response [201]>

If everything went right, you will receive a 201-Resonse_ and the table has
been created.

.. note::

    The OEP will automatically grant the 'admin'-permissions on this
    table to your user.

.. doctest::

    >>> result = requests.get(oep_url+'/api/v0/schema/sandbox/tables/example_table/columns')
    >>> result.status_code
    200
    >>> json_result = result.json()
    >>> json_result['id'] == {'character_maximum_length': None, 'maximum_cardinality': None, 'is_nullable': False, 'data_type': 'bigint', 'numeric_precision': 64, 'character_octet_length': None, 'interval_type': None, 'dtd_identifier': '1', 'interval_precision': None, 'numeric_scale': 0, 'is_updatable': True, 'datetime_precision': None, 'ordinal_position': 1, 'column_default': "nextval('sandbox.example_table_id_seq'::regclass)", 'numeric_precision_radix': 2}
    True
    >>> json_result['geom'] == {'column_default': None, 'character_maximum_length': None, 'maximum_cardinality': None, 'is_nullable': True, 'data_type': 'geometry', 'numeric_precision': None, 'character_octet_length': None, 'interval_type': None, 'dtd_identifier': '3', 'interval_precision': None, 'numeric_scale': None, 'is_updatable': True, 'datetime_precision': None, 'ordinal_position': 3, 'numeric_precision_radix': None}
    True
    >>> json_result['name'] == {'character_maximum_length': 50, 'maximum_cardinality': None, 'is_nullable': True, 'data_type': 'character varying', 'numeric_precision': None, 'character_octet_length': 200, 'interval_type': None, 'dtd_identifier': '2', 'interval_precision': None, 'numeric_scale': None, 'is_updatable': True, 'datetime_precision': None, 'ordinal_position': 2, 'column_default': None, 'numeric_precision_radix': None}
    True


.. _200-Resonse: https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
.. _201-Resonse: https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html

Insert data
===========

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
        https://openenergy-platform.org//api/v0/schema/sandbox/tables/example_table/rows/

**python**:

.. doctest::

    >>> import requests
    >>> data = {"query": {"name": "John Doe"}}
    >>> result = requests.post(oep_url+'/api/v0/schema/sandbox/tables/example_table/rows/new', json=data, headers={'Authorization': 'Token %s'%your_token} )
    >>> result.status_code
    201
    >>> result = requests.get(oep_url+'/api/v0/schema/sandbox/tables/example_table/rows/')
    >>> json_result = result.json()
    >>> json_result[-1]["id"] # Show the id of the new row
    1

Alternatively, we can specify that the new row should be stored under id 12:

**python**:

.. doctest::

    >>> import requests
    >>> data = {"query": {"name": "Mary Doe XII"}}
    >>> result = requests.put(oep_url+'/api/v0/schema/sandbox/tables/example_table/rows/12', json=data, headers={'Authorization': 'Token %s'%your_token} )
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

.. note::

    In order to insert new data, or perfom any other actions that alter the data
    state, you need the 'write'-permission for the respective table. Permissions can
    be granted by a user with 'admin'-permissions in the OEP web interface.

Select data
===========

You can insert data into a specific table by sending a GET-request to its
`/rows` subresource.
No authorization is required to do so.

**curl**::

    curl
        -X GET
        https://openenergy-platform.org/api/v0/schema/sandbox/tables/example_table/rows/

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

    >>> result = requests.get(oep_url+'/api/v0/schema/sandbox/tables/example_table/rows/', )
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

    >>> result = requests.get(oep_url+"/api/v0/schema/sandbox/tables/example_table/rows/?where=name=John+Doe", )
    >>> result.status_code
    200
    >>> json_result = result.json()
    >>> json_result == [{'id': 1, 'name': 'John Doe', 'geom': None}]
    True

.. doctest::

    >>> result = requests.get(oep_url+"/api/v0/schema/sandbox/tables/example_table/rows/1", )
    >>> result.status_code
    200
    >>> json_result = result.json()
    >>> json_result == {'id': 1, 'name': 'John Doe', 'geom': None}
    True

.. doctest::

    >>> result = requests.get(oep_url+"/api/v0/schema/sandbox/tables/example_table/rows/?offset=1")
    >>> result.status_code
    200
    >>> json_result = result.json()
    >>> json_result == [{'id': 12, 'name': 'Mary Doe XII', 'geom': None}]
    True

.. doctest::

    >>> result = requests.get(oep_url+"/api/v0/schema/sandbox/tables/example_table/rows/?column=name&column=id")
    >>> result.status_code
    200
    >>> json_result = result.json()
    >>> json_result == [{'id': 1, 'name': 'John Doe'},{'id': 12, 'name': 'Mary Doe XII'}]
    True

Add columns table
=================

.. doctest::

    >>> data = {'query':{'data_type': 'varchar', 'character_maximum_length': 30}}
    >>> result = requests.put(oep_url+"/api/v0/schema/sandbox/tables/example_table/columns/first_name", json=data, headers={'Authorization': 'Token %s'%your_token})
    >>> result.status_code
    201

.. doctest::

    >>> result = requests.get(oep_url+"/api/v0/schema/sandbox/tables/example_table/columns/first_name")
    >>> result.status_code
    200
    >>> result.json() == {'numeric_scale': None, 'numeric_precision_radix': None, 'is_updatable': True, 'maximum_cardinality': None, 'character_maximum_length': 30, 'character_octet_length': 120, 'ordinal_position': 4, 'is_nullable': True, 'interval_type': None, 'data_type': 'character varying', 'dtd_identifier': '4', 'column_default': None, 'datetime_precision': None, 'interval_precision': None, 'numeric_precision': None}
    True

Alter data
==========

Our current table looks as follows:

+-----------------+-------------------+-----------------------+------------------------+
| *id*: bigserial | name: varchar(50) | geom: geometry(Point) | first_name: varchar(30)|
+=================+===================+=======================+========================+
|             1   | John Doe          | NULL                  | NULL                   |
+-----------------+-------------------+-----------------------+------------------------+
|             12  | Mary Doe XII      | NULL                  | NULL                   |
+-----------------+-------------------+-----------------------+------------------------+

Our next task is to distribute for and last name to the different columns:

.. doctest::

    >>> result = requests.get(oep_url+'/api/v0/schema/sandbox/tables/example_table/rows/') # Load the names via GET
    >>> result.status_code
    200
    >>> for row in result.json():
    ...     first_name, last_name = str(row['name']).split(' ', 1) # Split the names at the first space
    ...     data = {'query': {'name': last_name, 'first_name': first_name}} # Build the data dictionary and post it to /rows/<id>
    ...     result = requests.post(oep_url+'/api/v0/schema/sandbox/tables/example_table/rows/{id}'.format(id=row['id']), json=data, headers={'Authorization': 'Token %s'%your_token})
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
============

Currently, rows are allowed that contain no first name. In order to prohibit
such behaviour, we have to set column `first_name` to `NOT NULL`. Such `ALTER
TABLE` commands can be executed by POST-ing a dictionary with the corresponding
values to the column's resource:

.. doctest::

    >>> data = {'query': {'is_nullable': False}}
    >>> result = requests.post(oep_url+"/api/v0/schema/sandbox/tables/example_table/columns/first_name", json=data, headers={'Authorization': 'Token %s'%your_token} )
    >>> result.status_code
    200

We can check, whether your command worked by retrieving the corresponding resource:

.. doctest::

    >>> result = requests.get(oep_url+"/api/v0/schema/sandbox/tables/example_table/columns/first_name")
    >>> result.status_code
    200
    >>> json_result = result.json()
    >>> json_result['is_nullable']
    False

After prohibiting null-values in the first name column, such rows can not be
added anymore.

.. doctest::

    >>> import requests
    >>> data = {"query": {"name": "McPaul"}}
    >>> result = requests.post(oep_url+'/api/v0/schema/sandbox/tables/example_table/rows/new', json=data, headers={'Authorization': 'Token %s'%your_token} )
    >>> result.status_code
    400
    >>> result.json()['reason']
    'Action violates not-null constraint on first_name. Failing row was (McPaul)'


Delete rows
***********

In order to delete rows, you need the 'delete'-permission on the respective
table. The permissions can be granted by an admin in the OEP web interface.

.. doctest::

    >>> import requests
    >>> data = {"query": {"name": "McPaul"}}
    >>> result = requests.delete(oep_url+'/api/v0/schema/sandbox/tables/example_table/rows/1', json=data, headers={'Authorization': 'Token %s'%your_token} )
    >>> result.status_code
    200
    >>> result = requests.get(oep_url+'/api/v0/schema/sandbox/tables/example_table/rows/1')
    >>> result.status_code
    404


Metadata
********

The OEP gives the opportunity to publish datasets and annotate it with important
information. You can query this metadata

.. doctest::

    >>> import requests
    >>> result = requests.get(oep_url+'/api/v0/schema/sandbox/tables/example_table/meta/')
    >>> result.status_code
    200
    >>> result.json() == {'id': 'sandbox.example_table', 'metaMetadata': {'metadataVersion': 'OEP-1.5.2', 'metadataLicense': {'name': 'CC0-1.0', 'title': 'Creative Commons Zero v1.0 Universal', 'path': 'https://creativecommons.org/publicdomain/zero/1.0/'}},  "_comment": {"metadata": "Metadata documentation and explanation (https://github.com/OpenEnergyPlatform/oemetadata)", "dates": "Dates and time must follow the ISO8601 including time zone (YYYY-MM-DD or YYYY-MM-DDThh:mm:ss±hh)", "units": "Use a space between numbers and units (100 m)", "languages": "Languages must follow the IETF (BCP47) format (en-GB, en-US, de-DE)", "licenses": "License name must follow the SPDX License List (https://spdx.org/licenses/)", "review": "Following the OEP Data Review (https://github.com/OpenEnergyPlatform/data-preprocessing/blob/master/data-review/manual/review_manual.md)", "null": "If not applicable use: null", "todo": "If a value is not yet available, use: todo"}}
    True

Note that the returned metadata differs from the metadata passed when creating
the table. This is because the OEP autocompletes missing fields. You can fill
those fields to make you data more easily accessible. You can also set metadata
on existing tables via `POST`-requests (granted that you have write-permissions):

.. doctest::

    >>> import requests
    >>> data = {
    ... "id": "sandbox.example_table",
    ... "name": "Human-readable name",
    ... "description": "A verbose description of this dataset",
    ... "language": [
    ...     "eng-uk"
    ...    ],
    ...    "keywords": [
    ...        "test"
    ...    ],
    ...    "publicationDate": "2020-02-06",
    ...    "context": {
    ...        "homepage": "example.com",
    ...        "documentation": "doc.example.com",
    ...        "sourceCode": "src.example.com",
    ...        "contact": "example.com",
    ...        "grantNo": "0",
    ...        "fundingAgency": "test agency",
    ...        "fundingAgencyLogo": "http://www.example.com/logo.png",
    ...        "publisherLogo": "http://www.example.com/logo2.png"
    ...    },
    ...    "licenses": [
    ...        {
    ...            "name": "CC0-1.0",
    ...            "title": "Creative Commons Zero v1.0 Universal",
    ...            "path": "https://creativecommons.org/publicdomain/zero/1.0/legalcode",
    ...            "instruction": "You are free: To Share, To Create, To Adapt",
    ...            "attribution": "© Reiner Lemoine Institut"
    ...        }
    ...    ],
    ...    "metaMetadata": {
    ...        "metadataVersion": "OEP-1.5.1",
    ...        "metadataLicense": {
    ...            "name": "CC0-1.0",
    ...            "title": "Creative Commons Zero v1.0 Universal",
    ...            "path": "https://creativecommons.org/publicdomain/zero/1.0/"
    ...        }
    ...    },
    ...    "_comment": {
    ...        "metadata": "Metadata documentation and explanation (https://github.com/OpenEnergyPlatform/oemetadata)",
    ...        "dates": "Dates and time must follow the ISO8601 including time zone (YYYY-MM-DD or YYYY-MM-DDThh:mm:ss±hh)",
    ...        "units": "Use a space between numbers and units (100 m)",
    ...        "languages": "Languages must follow the IETF (BCP47) format (en-GB, en-US, de-DE)",
    ...        "licenses": "License name must follow the SPDX License List (https://spdx.org/licenses/)",
    ...        "review": "Following the OEP Data Review (https://github.com/OpenEnergyPlatform/data-preprocessing/blob/master/data-review/manual/review_manual.md)",
    ...        "null": "If not applicable use: null",
    ...        "todo": "If a value is not yet available, use: todo"
    ...    }
    ... }
    >>> result = requests.post(oep_url+'/api/v0/schema/sandbox/tables/example_table/meta/', json=data, headers={'Authorization': 'Token %s'%your_token})
    >>> result.status_code
    200


Delete tables
*************

In order to delete rows, you need the 'admin'-permission on the respective
table. The permissions can be granted by an admin in the OEP web interface.

.. doctest::

    >>> import requests
    >>> requests.delete(oep_url+'/api/v0/schema/sandbox/tables/example_table', headers={'Authorization': 'Token %s'%your_token} )
    <Response [200]>
    >>> requests.get(oep_url+'/api/v0/schema/sandbox/tables/example_table')
    <Response [404]>

For more advanced commands read :doc:`advanced`

Handling Arrays
***************

The underlying OpenEnergy Database is a Postgres database. Thus, it supports
Array-typed fields.

.. doctest::

    >>> import requests
    >>> data = { "query": { "columns": [ { "name":"id", "data_type": "bigserial", "is_nullable": "NO" },{ "name":"arr", "data_type": "int[]"},{ "name":"geom", "data_type": "geometry(point)" } ], "constraints": [ { "constraint_type": "PRIMARY KEY", "constraint_parameter": "id" } ] } }
    >>> requests.put(oep_url+'/api/v0/schema/sandbox/tables/example_table/', json=data, headers={'Authorization': 'Token %s'%your_token} )
    <Response [201]>

.. doctest::

    >>> import requests
    >>> data = {"query": {"arr": [1,2,3]}}
    >>> result = requests.post(oep_url+'/api/v0/schema/sandbox/tables/example_table/rows/new', json=data, headers={'Authorization': 'Token %s'%your_token} )
    >>> result.status_code
    201
    >>> result = requests.get(oep_url+'/api/v0/schema/sandbox/tables/example_table/rows/1')
    >>> json_result = result.json()
    >>> json_result['arr']
    [1, 2, 3]

.. testcleanup::

    import requests
    response = requests.delete(oep_url+'/api/v0/schema/sandbox/tables/example_table/', json=data, headers={'Authorization': 'Token %s'%your_token} )
    assert response.status_code == 200, response
