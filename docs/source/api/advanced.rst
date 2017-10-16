*********************
Advanced API features
*********************

.. testsetup::

    oep_url = 'http://localhost:8000'
    from oeplatform.securitysettings import token_test_user as your_token
    from shapely import wkt
    from django.contrib.gis.geos import Point
    import json

.. doctest::

    >>> import requests
    >>> data = { "query": { "columns": [ { "name":"id", "data_type": "bigserial", "is_nullable": "NO" },{ "name":"name", "data_type": "varchar", "character_maximum_length": "50" },{ "name":"geom", "data_type": "geometry(point)" } ], "constraints": [ { "constraint_type": "PRIMARY KEY", "constraint_parameter": "id" } ] } }
    >>> requests.put(oep_url+'/api/v0/schema/sandbox/tables/example_table/', json=data, headers={'Authorization': 'Token %s'%your_token} )
    <Response [201]>
    >>> data = {"query": [{"id": i, "name": "John Doe"+str(i), "geom":str(Point(0,i,srid=32140))} for i in range(10)]}
    >>> requests.post(oep_url+'/api/v0/schema/sandbox/tables/example_table/rows/new', json=data, headers={'Authorization': 'Token %s'%your_token} )
    <Response [201]>

The basic REST-API as described in :doc:`how_to` freatures functionalities for
simple CRUD-tasks.

This may be sufficient for data manipulation, but the underlying Database
Management System features a much richer environment for data select scripts.

You can issue a POST-request to the URL `advanced/v0/search`. The actual query
described as a JSON string inside this request. This page will describe the
general make-up of this JSON structure.

Syntax Specification
====================

.. _select-objects:

Select
------

A query object **MUST** contain

    * :code:`from` : A :ref:`From item <from-objects>`

It **MAY** contain the folowing directives. If not present, they will be
replaced by the stated defaults:

    * :code:`distrinct`: :code:`true` | :code:`false` (default: :code:`false`)
    * :code:`fields`: List of :ref:`Expressions <expression-objects>` (If not present, will be interpreted as :code:`*`), that **MAY** contain the following additional fields:
        * :code:`as`: A string
    * :code:`where`: A list of :ref:`Expressions <expression-objects>` that return a truth value (default: [])
    * :code:`group_by`: List of :ref:`Expressions <expression-objects>` (default: [])
    * :code:`having`: A list of :ref:`Expressions <expression-objects>` that return a truth value (default: [])
    * :code:`select`: A list of dictionaries that **MUST** contain:
        * :code:`query`: A :ref:`Select object <select-objects>`
        * :code:`type`: :code:`union` | :code:`intersect` | :code:`except`
    * :code:`order_by`: List of :ref:`Expressions <expression-objects>` (default: []), that **MAY** contain the following additional fields:
        * :code:`ordering`: :code:`asc` | :code:`desc` (default: :code:`asc`)
    * :code:`limit`: Integer
    * :code:`offset`: Integer


.. _expression-objects:

Expressions
-----------

An expression object **MUST** contain:
    * :code:`type`: A string as specified below

The depending on the :code:`type` the dictionary may have a a different structure:
    * :code:`column`: A column expression **MUST** contain the following fields:
        * :code:`column`: Name of the column
    * :code:`grouping`: A grouping expression **MUST** contain the following fields:
        * :code:`grouping`: A list of :ref:`Expressions <expression-objects>`
    * :code:`operator`: An operator expression **MUST** contain the following fields:
        * :code:`operator`: A string consisting of one of the following operators:
            * Unary operators: :code:`NOT`
            * Binary operators: :code:`EQUALS` | :code:`=` :code:`GREATER` | :code:`>` | :code:`LOWER` | :code:`<` | :code:`NOTEQUAL` | :code:`<>` | :code:`!=` | :code:`NOTGREATER` | :code:`<=` | :code:`NOTLOWER` | :code:`>=`
            * n-ary operators: :code:`AND` | :code:`OR`
        * :code:`operands`: A list of :ref:`Expressions <expression-objects>`
    * :code:`function`: A function expression **MUST** contain the following fields:
        * :code:`function`: The name of the function. All functions implemented in sqlalchemy and geoalchemy are available.
        * :code:`operands`: A list of :ref:`Expressions <expression-objects>`
    * :code:`value`: A constant value

.. _from-objects:

From items
----------

A from object **MUST** contain:
    * :code:`type`: A string as specified below

The depending on the :code:`type` the dictionary may have a a different structure:
    * :code:`table`: A table item **MUST** contain the following fields:
        * :code:`table`: Name of the table
    A table item **MAY** contain the following fields:
        * :code:`schema`: Name of the schema
        * :code:`only`: :code:`true` | :code:`false` (default: :code:`false`)
    * :code:`select`: A select item **MUST** contain the following fields:
        * :code:`query`: A :ref:`Select object <select-objects>`
    * :code:`join`: A join item **MUST** contain the following fields:
        * :code:`left`: A :ref:`From item <from-objects>`
        * :code:`right`: A :ref:`From item <from-objects>`
        A join item **MAY** contain the following fields:
        * :code:`is_outer`: :code:`true` | :code:`false` (default: :code:`false`)
        * :code:`is_full`: :code:`true` | :code:`false` (default: :code:`false`)
        * :code:`on`: An :ref:`Expression <expression-objects>` that returns a truth value

Each from item **MAY** contain the following fields regardless of its type:
    * :code:`alias`: An alias for this item

Examples
========

For starters we will issue a simple request to check which data is available. In order to do so,
we use the following query::

    {
      "fields":[
        "id",
        "name"
      ],
      "from":{
        'type': 'table',
        'table': 'example_table',
        'schema':"sandbox"
      }
    }


.. doctest::

    >>> import requests
    >>> data = { "query": {"fields": ["id", "name"], "from":{'type': 'table', 'table': 'example_table', 'schema':"sandbox"}}}
    >>> response = requests.post(oep_url+'/api/v0/advanced/search', json=data )
    >>> response.json()['data']
    [[0, 'John Doe0'], [1, 'John Doe1'], [2, 'John Doe2'], [3, 'John Doe3'], [4, 'John Doe4'], [5, 'John Doe5'], [6, 'John Doe6'], [7, 'John Doe7'], [8, 'John Doe8'], [9, 'John Doe9']]

In order to get all entries with an id less than 3, we could extend above query
by a where clause::

    'where': {
      'operands': [
        {
          'type': 'column',
          'column':'id'
        },
        3
      ],
      'operator': '<',
      'type': 'operator'
    }




.. doctest::

    >>> import requests
    >>> data = { "query": {"fields": ["id", "name"], "from":{'type': 'table', 'table': 'example_table', 'schema':"sandbox"}, 'where': {'operands': [{'type': 'column', 'column':'id'}, 3], 'operator': '<', 'type': 'operator'} }}
    >>> response = requests.post(oep_url+'/api/v0/advanced/search', json=data)
    >>> response.json()['data']
    [[0, 'John Doe0'], [1, 'John Doe1'], [2, 'John Doe2']]

You can add several conditons as a list. Those will be interpreted as a conjunction:

.. doctest::

    >>> import requests
    >>> data = { "query": {"fields": ["id", "name"], "from":{'type': 'table', 'table': 'example_table', 'schema':"sandbox"}, 'where': [{'operands': [{'type': 'column', 'column':'id'}, 3], 'operator': '<', 'type': 'operator'}, {'operands': [{'type': 'column', 'column':'id'}, 1], 'operator': '>', 'type': 'operator'} ] }}
    >>> response = requests.post(oep_url+'/api/v0/advanced/search', json=data)
    >>> response.json()['data']
    [[2, 'John Doe2']]

Functions
---------

You can also alter all functions that are implemented in sqlalchemy and
geoalchemy2 to alter the results of your query. In the following example we
simply add two to every id:

.. doctest::

    >>> import requests
    >>> data = { "query": {"fields": ['id', {'type': 'function', 'function': '+', 'operands':[{'type': 'column', 'column': 'id'}, 2]}], "from":{'type': 'table', 'table': 'example_table', 'schema':"sandbox"}}}
    >>> response = requests.post(oep_url+'/api/v0/advanced/search', json=data)
    >>> response.json()['data']
    [[0, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7], [6, 8], [7, 9], [8, 10], [9, 11]]

Functions are especially usefull if you want to return geodata in a specific
format. In the following we obtain the WKT representation of our data:

.. doctest::

    >>> import requests
    >>> data = { "query": {"fields": ['id', {'type': 'function', 'function': 'ST_AsText', 'operands':[{'type': 'column', 'column': 'geom'}]}], "from":{'type': 'table', 'table': 'example_table', 'schema':"sandbox"}}}
    >>> response = requests.post(oep_url+'/api/v0/advanced/search', json=data)
    >>> data = response.json()['data']
    >>> data[0]
    [0, 'POINT(0 0)']
    >>> all(geom == 'POINT(0 %d)'%pid for pid, geom in data)
    True

... or the geoJSON representation ...

.. doctest::

    >>> import requests
    >>> data = { "query": {"fields": ['id', {'type': 'function', 'function': 'ST_AsGeoJSON', 'operands':[{'type': 'column', 'column': 'geom'}, 4236]}], "from":{'type': 'table', 'table': 'example_table', 'schema':"sandbox"}}}
    >>> response = requests.post(oep_url+'/api/v0/advanced/search', json=data)
    >>> data = response.json()['data']
    >>> data[0]
    [0, '{"type":"Point","coordinates":[0,0]}']
    >>> all(pid == json.loads(geom)['coordinates'][1] for pid, geom in data)
    True

Joins
-----

Joins can be queried by using the corresponding from-item::

    {
     "from":{
      'type': 'join',
      'left': {
       'type': 'table',
       'table': 'example_table',
       'schema':"sandbox",
       "alias":"a"
       },
      'right': {
       'type': 'table',
       'table': 'example_table',
       'schema':"sandbox",
       "alias":"b"
       },
      'on': {
       'operands': [
        {'type': 'column', 'column':'id', 'table': 'a'},
        {'type': 'column', 'column':'id', 'table': 'b'}
        ],
       'operator': '<',
       'type': 'operator'
       }
      }
     }


.. doctest::

    >>> import requests
    >>> data = { "query": {"from":{'type': 'join','left': {'type': 'table', 'table': 'example_table', 'schema':"sandbox", "alias":"a"},'right': {'type': 'table', 'table': 'example_table', 'schema':"sandbox", "alias":"b"},'on': {'operands': [{'type': 'column', 'column':'id', 'table': 'a'}, {'type': 'column', 'column':'id', 'table': 'b'}], 'operator': '<', 'type': 'operator'}}}}
    >>> response = requests.post(oep_url+'/api/v0/advanced/search', json=data)
    >>> response.json()['data']
    [[0, 'John Doe0', '01010000208C7D000000000000000000000000000000000000', 1, 'John Doe1', '01010000208C7D00000000000000000000000000000000F03F'], [0, 'John Doe0', '01010000208C7D000000000000000000000000000000000000', 2, 'John Doe2', '01010000208C7D000000000000000000000000000000000040'], [0, 'John Doe0', '01010000208C7D000000000000000000000000000000000000', 3, 'John Doe3', '01010000208C7D000000000000000000000000000000000840'], [0, 'John Doe0', '01010000208C7D000000000000000000000000000000000000', 4, 'John Doe4', '01010000208C7D000000000000000000000000000000001040'], [0, 'John Doe0', '01010000208C7D000000000000000000000000000000000000', 5, 'John Doe5', '01010000208C7D000000000000000000000000000000001440'], [0, 'John Doe0', '01010000208C7D000000000000000000000000000000000000', 6, 'John Doe6', '01010000208C7D000000000000000000000000000000001840'], [0, 'John Doe0', '01010000208C7D000000000000000000000000000000000000', 7, 'John Doe7', '01010000208C7D000000000000000000000000000000001C40'], [0, 'John Doe0', '01010000208C7D000000000000000000000000000000000000', 8, 'John Doe8', '01010000208C7D000000000000000000000000000000002040'], [0, 'John Doe0', '01010000208C7D000000000000000000000000000000000000', 9, 'John Doe9', '01010000208C7D000000000000000000000000000000002240'], [1, 'John Doe1', '01010000208C7D00000000000000000000000000000000F03F', 2, 'John Doe2', '01010000208C7D000000000000000000000000000000000040'], [1, 'John Doe1', '01010000208C7D00000000000000000000000000000000F03F', 3, 'John Doe3', '01010000208C7D000000000000000000000000000000000840'], [1, 'John Doe1', '01010000208C7D00000000000000000000000000000000F03F', 4, 'John Doe4', '01010000208C7D000000000000000000000000000000001040'], [1, 'John Doe1', '01010000208C7D00000000000000000000000000000000F03F', 5, 'John Doe5', '01010000208C7D000000000000000000000000000000001440'], [1, 'John Doe1', '01010000208C7D00000000000000000000000000000000F03F', 6, 'John Doe6', '01010000208C7D000000000000000000000000000000001840'], [1, 'John Doe1', '01010000208C7D00000000000000000000000000000000F03F', 7, 'John Doe7', '01010000208C7D000000000000000000000000000000001C40'], [1, 'John Doe1', '01010000208C7D00000000000000000000000000000000F03F', 8, 'John Doe8', '01010000208C7D000000000000000000000000000000002040'], [1, 'John Doe1', '01010000208C7D00000000000000000000000000000000F03F', 9, 'John Doe9', '01010000208C7D000000000000000000000000000000002240'], [2, 'John Doe2', '01010000208C7D000000000000000000000000000000000040', 3, 'John Doe3', '01010000208C7D000000000000000000000000000000000840'], [2, 'John Doe2', '01010000208C7D000000000000000000000000000000000040', 4, 'John Doe4', '01010000208C7D000000000000000000000000000000001040'], [2, 'John Doe2', '01010000208C7D000000000000000000000000000000000040', 5, 'John Doe5', '01010000208C7D000000000000000000000000000000001440'], [2, 'John Doe2', '01010000208C7D000000000000000000000000000000000040', 6, 'John Doe6', '01010000208C7D000000000000000000000000000000001840'], [2, 'John Doe2', '01010000208C7D000000000000000000000000000000000040', 7, 'John Doe7', '01010000208C7D000000000000000000000000000000001C40'], [2, 'John Doe2', '01010000208C7D000000000000000000000000000000000040', 8, 'John Doe8', '01010000208C7D000000000000000000000000000000002040'], [2, 'John Doe2', '01010000208C7D000000000000000000000000000000000040', 9, 'John Doe9', '01010000208C7D000000000000000000000000000000002240'], [3, 'John Doe3', '01010000208C7D000000000000000000000000000000000840', 4, 'John Doe4', '01010000208C7D000000000000000000000000000000001040'], [3, 'John Doe3', '01010000208C7D000000000000000000000000000000000840', 5, 'John Doe5', '01010000208C7D000000000000000000000000000000001440'], [3, 'John Doe3', '01010000208C7D000000000000000000000000000000000840', 6, 'John Doe6', '01010000208C7D000000000000000000000000000000001840'], [3, 'John Doe3', '01010000208C7D000000000000000000000000000000000840', 7, 'John Doe7', '01010000208C7D000000000000000000000000000000001C40'], [3, 'John Doe3', '01010000208C7D000000000000000000000000000000000840', 8, 'John Doe8', '01010000208C7D000000000000000000000000000000002040'], [3, 'John Doe3', '01010000208C7D000000000000000000000000000000000840', 9, 'John Doe9', '01010000208C7D000000000000000000000000000000002240'], [4, 'John Doe4', '01010000208C7D000000000000000000000000000000001040', 5, 'John Doe5', '01010000208C7D000000000000000000000000000000001440'], [4, 'John Doe4', '01010000208C7D000000000000000000000000000000001040', 6, 'John Doe6', '01010000208C7D000000000000000000000000000000001840'], [4, 'John Doe4', '01010000208C7D000000000000000000000000000000001040', 7, 'John Doe7', '01010000208C7D000000000000000000000000000000001C40'], [4, 'John Doe4', '01010000208C7D000000000000000000000000000000001040', 8, 'John Doe8', '01010000208C7D000000000000000000000000000000002040'], [4, 'John Doe4', '01010000208C7D000000000000000000000000000000001040', 9, 'John Doe9', '01010000208C7D000000000000000000000000000000002240'], [5, 'John Doe5', '01010000208C7D000000000000000000000000000000001440', 6, 'John Doe6', '01010000208C7D000000000000000000000000000000001840'], [5, 'John Doe5', '01010000208C7D000000000000000000000000000000001440', 7, 'John Doe7', '01010000208C7D000000000000000000000000000000001C40'], [5, 'John Doe5', '01010000208C7D000000000000000000000000000000001440', 8, 'John Doe8', '01010000208C7D000000000000000000000000000000002040'], [5, 'John Doe5', '01010000208C7D000000000000000000000000000000001440', 9, 'John Doe9', '01010000208C7D000000000000000000000000000000002240'], [6, 'John Doe6', '01010000208C7D000000000000000000000000000000001840', 7, 'John Doe7', '01010000208C7D000000000000000000000000000000001C40'], [6, 'John Doe6', '01010000208C7D000000000000000000000000000000001840', 8, 'John Doe8', '01010000208C7D000000000000000000000000000000002040'], [6, 'John Doe6', '01010000208C7D000000000000000000000000000000001840', 9, 'John Doe9', '01010000208C7D000000000000000000000000000000002240'], [7, 'John Doe7', '01010000208C7D000000000000000000000000000000001C40', 8, 'John Doe8', '01010000208C7D000000000000000000000000000000002040'], [7, 'John Doe7', '01010000208C7D000000000000000000000000000000001C40', 9, 'John Doe9', '01010000208C7D000000000000000000000000000000002240'], [8, 'John Doe8', '01010000208C7D000000000000000000000000000000002040', 9, 'John Doe9', '01010000208C7D000000000000000000000000000000002240']]


.. testcleanup::

    import requests
    requests.delete(oep_url+'/api/v0/schema/sandbox/tables/example_table', headers={'Authorization': 'Token %s'%your_token} )


