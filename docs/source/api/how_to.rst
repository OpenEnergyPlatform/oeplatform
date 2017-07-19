How to work with the API - An example
=====================================


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

We want to create the following table:

+---------+--------------+-----------------------+
| id: int | name: string | geom: geometry(Point) |
+=========+==============+=======================+
|         |              |                       |
+---------+--------------+-----------------------+

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
                    ]
                }
            }'
        oep.iks.cs.ovgu.de/api/v0/schema/example_schema/tables/example_table/

If everything went right, you will receive a 200-Resonse_ and the table has
been created.

.. _200-Resonse: https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html

Insert data
***********

You can insert data into a specific table by sending a POST-request to its
`/rows` subresource. The `query` part of the sent data contians the row you want
to insert in form of a JSON-dictionary:::

    {
        'name_of_column_1': 'value_in_column_1',
        'name_of_column_2': 'value_in_column_2',
        ...
    }

In the following example, we want to add a row containing
just the name "John Doe":

**curl**::

    curl
        -X POST
        -H "Content-Type: application/json"
        -H 'Authorization: Token <your-token>'
        -d '{"query": {"name": "John Doe"}}'
        oep.iks.cs.ovgu.de/api/v0/schema/model_draft/tables/example_table/rows/

Again, a 200-Resonse_ indicates success.
