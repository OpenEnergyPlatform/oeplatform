*********************
Advanced API features
*********************

.. testsetup::

    oep_url = 'http://localhost:8000'
    from oeplatform.securitysettings import token_test_user as your_token


.. doctest::

    >>> import requests
    >>> data = { "query": { "columns": [ { "name":"id", "data_type": "bigserial", "is_nullable": "NO" },{ "name":"name", "data_type": "varchar", "character_maximum_length": "50" },{ "name":"geom", "data_type": "geometry(point)" } ], "constraints": [ { "constraint_type": "PRIMARY KEY", "constraint_parameter": "id" } ] } }
    >>> requests.put(oep_url+'/api/v0/schema/sandbox/tables/example_table/', json=data, headers={'Authorization': 'Token %s'%your_token} )
    <Response [201]>
    >>> data = {"query": {"name": "John Doe"}}
    >>> requests.post(oep_url+'/api/v0/schema/sandbox/tables/example_table/rows/new', json=data, headers={'Authorization': 'Token %s'%your_token} )
    <Response [201]>
    >>> data = {"query": {"name": "Mary Doe"}}
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

    * :code:`from` : A from item

It **MAY** contain the folowing directives. If not present, they will be
replaced by the stated defaults:

    * :code:`distrinct`: :code:`true` | :code:`false` (default: :code:`false`)
    * :code:`fields`: List of :ref:`Expressions <expression-objects>` (If not present, will be interpreted as :code:`*`), that **MAY** contain the following additional fields:
        * :code:`as`: A string
    * :code:`where`: List of :ref:`Conditions <condition-objects>` (default: [])
    * :code:`group_by`: List of :ref:`Groupings <grouping-objects>` (default: [])
    * :code:`having`: List of :ref:`Conditions <condition-objects>` (default: [])
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


.. condition-objects:

Conditions
----------


Simple select syntax
====================

.. doctest::

    >>> import requests
    >>> data = { "query": {"fields": ["id", "name"], "from":{'type': 'table', 'table': 'example_table', 'schema':"sandbox"}}}
    >>> response = requests.post(oep_url+'/api/v0/advanced/search', json=data, headers={'Authorization': 'Token %s'%your_token} )
    >>> response.json()['data']
    [[1, 'John Doe'], [2, 'Mary Doe']]
From-items
==========

.. doctest::

    >>> import requests
    >>> requests.delete(oep_url+'/api/v0/schema/sandbox/tables/example_table', headers={'Authorization': 'Token %s'%your_token} )
    <Response [200]>