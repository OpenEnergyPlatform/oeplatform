Data interface (REST)
=====================

Data Structures
---------------

### Constraint Definition

constraint\_definition (Dictonary)

:   

    Specifies a definition of a constraint.

    :   -   `action` Action of constraint (e.g. ADD, DROP)
        -   `constraint_type` Type of constraint (e.g. UNIQUE, PRIMARY
            KEY, FOREIGN KEY)
        -   `constraint_name` Name of constraint.
        -   `constraint_parameter` Parameter of constraint.
        -   `reference_table` Name of reference table, can be None.
        -   `reference_column` Name of reference column, can be None.

### Column Definition

column\_definition (Dictonary)

:   

    Specifies a definition of a column.

    :   -   `name` Name of column.
        -   `new_name` New name of column, can be None.
        -   `data_type` New datatype of column, can be None.
        -   `is_nullable` New null value of column, can be None.
        -   `character_maximum_length` New data length of column, can be
            None.

### Response Definition

response\_dictonary (Dictonary)

:   

    Describes the result of an api action.

    :   -   `success (Boolean)` Result of Action
        -   `error (String)` Error Message
        -   `http_status (Integer)` HTTP status code
            (<https://en.wikipedia.org/wiki/List_of_HTTP_status_codes>)

Table (RESTful)
---------------

URL: /schema/{schema}/table/{table}

### GET

Reference needed.

### PUT

Creates a new table in database. JSON should contain a constraint
definition array and a column definition array.

Example:

``` json
{
  "constraints": [
    {
      "constraint_type": "FOREIGN KEY",
      "constraint_name": "fkey_schema_table_database_id",
      "constraint_parameter": "database_id",
      "reference_table": "example.table",
      "reference_column": "database_id_ref"
    },
    {
      "constraint_type": "PRIMARY KEY",
      "constraint_name": "pkey_schema_table_id",
      "constraint_parameter": "id",
      "reference_table": null,
      "reference_column": null
    }
  ],
  "columns": [
    {
      "name": "id",
      "data_type": "int",
      "is_nullable": "YES",
      "character_maximum_length": null
    },
    {
      "name": "name",
      "data_type": "character varying",
      "is_nullable": "NO",
      "character_maximum_length": 50
    }
  ]
}
```

### POST

JSON should contain a column or constraint definition. Additionally
`action` and `type` should be mentioned.

-   `type` can be `constraint` or `column`.
-   `action` can be `ADD` and `DROP`.
-   `constraint_type` can be every constraint type supported by
    Postgres.
-   `reference_table` and `reference_column` can be null, if not
    necessary.

Example:

``` json
{
  "type" : "constraint",
  "action": "ADD",
  "constraint_type": "FOREIGN KEY",
  "constraint_name": "fkey_label",
  "constraint_parameter": "changed_name",
  "reference_table" : "reference.group_types",
  "reference_column" : "label"
}

{
  "type" : "column",
  "name" : "test_name",
  "newname" : "changed_name",
  "data_type": "character varying",
  "is_nullable": "NO",
  "character_maximum_length": 50
}
```

Rows (RESTful)
--------------

### GET

URL: `/schema/<schema>/tables/<table>/rows/`

You can use this part to get information from the database.

You can specify the following parameters in the url:

:   -   `columns (List)` List of selected columns, e.g. `id,name`

    -   

        `where (List)` List of where clauses, e.g. `id+OPERATOR+1+CONNECTOR+name+OPERATOR+georg`

        :   -   OPERATORS could be EQUAL, GREATER, LOWER, NOTEQUAL,
                NOTGREATER, NOTLOWER
            -   CONNECTORS could be AND, OR

    -   `orderby (List)` List of order columns, e.g. `name,code`

    -   `limit (Number)` Number of displayed items, e.g. `100`

    -   `offset (Number)` Number of offset from start, e.g. `10`


[^1]: The OEP is currently only supporting a non-compound integer
    primary key labeled \'id\'. Violation of this constraint might
    render the OEP unable to display the data stored in this table.
