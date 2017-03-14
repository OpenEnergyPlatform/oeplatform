=====================
Data interface (REST)
=====================


Data Structures
===============

Constraint Definition
---------------------

:constraint_definition (Dictonary):
    Specifies a definition of a constraint.
        * ``action`` Action of constraint (e.g. ADD, DROP)
        * ``constraint_type`` Type of constraint (e.g. UNIQUE, PRIMARY KEY, FOREIGN KEY)
        * ``constraint_name`` Name of constraint.
        * ``constraint_parameter`` Parameter of constraint.
        * ``reference_table`` Name of reference table, can be None.
        * ``reference_column`` Name of reference column, can be None.

Column Definition
-----------------

:column_definition (Dictonary):
    Specifies a definition of a column.
        * ``name`` Name of column.
        * ``new_name`` New name of column, can be None.
        * ``data_type`` New datatype of column, can be None.
        * ``is_nullable`` New null value of column, can be None.
        * ``character_maximum_length`` New data length of column, can be None.

Response Definition
-------------------

:response_dictonary (Dictonary):
    Describes the result of an api action.
        * ``success (Boolean)`` Result of Action
        * ``error (String)`` Error Message
        * ``http_status (Integer)`` HTTP status code (https://en.wikipedia.org/wiki/List_of_HTTP_status_codes)



Create a table
==============

.. [#idpk] The OEP is currently only supporting a non-compound integer primary
           key labeled 'id'. Violation of this constraint might render the OEP unable to
           display the data stored in this table.


Dictionary structure
--------------------

:schema (String):
    Specifies the schema name the table should be created in. If this
    schema does not exist it will be created.

:table (String):
    Specifies the name of the table to be created.

:fields (List):
    List specifying the columns of the new table (see `Field specification`_).

:constraints (List):
    List of additional constraints (see `Constraint specification`_).


Field specification
-------------------

:name (String):
    Name of the field

:type (String):
    Name of a valid `Postgresql type <https://www.postgresql.org/docs/8.4/static/datatype.html>`_

:pk (Bool):
    Specifies whether this column is a primary key. Be aware
    of [#idpk]_

Constraint specification
------------------------

Args:
    :name (String):
        Type of constraint. Possible values:

            * ``fk`` (see `Foreign key specification`_)
    :constraint (Dictionary):
        Dictionary as specified by the foreign key.


Foreign key specification
-------------------------

:schema (String):
    Name of the schema the referenced table is stored in

:table (String):
    Name of the referenced table

:field (String):
    Name of the referenced column

:on_delete (String):
    Specifies the behaviour if this field is deleted. Possible values:

        * ``cascade``
        * ``no action``
        * ``restrict``
        * ``set null``
        * ``set default``


Insert data
===========

:schema (String):
    Specifies the schema name the table should be created in. If this
    schema does not exist it will be created.

:table (String):
    Specifies the name of the table to be created.

:fields (List):
    List specifying the column names the date should be inserted in.

:values (List):
    Each element is a list of values that should be inserted. The number
    of elements must match the number of fields.

:returning (Bool):
    An expression that is evaluated and returned as result. If this
    entry is present the result of this expression is returned as in
    `Select Data`_.


Select data
===========

:all (Bool):
    Specifies whether all rows should be returned (default)

:distinct (Bool):
    Specifies whether only unique rows should be returned

:fields (List):
    The list of columns that should be returned (see select_field_spec_)

:where (List):
    The list of condition that should be considered (see select_condition_spec_)

:limit (Integer or 'all'):
    Specifies how many results should be returned. If 'all'
    is set all matching rows will be returned (default).

:offset (Integer):
    Specifies how many entries should be skipped before returning
    data


Binding the API to python
=========================

.. automodule:: api.views
    :members:

.. automodule:: api.actions
    :members: