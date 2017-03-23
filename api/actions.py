import json
import re
import traceback
from datetime import datetime

import sqlalchemy as sqla
from sqlalchemy import func, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import api.parser
import oeplatform.securitysettings as sec
from api import parser
from api import references

pgsql_qualifier = re.compile(r"^[\w\d_\.]+$")
_ENGINES = {}

Base = declarative_base()


class InvalidRequest(Exception):
    pass


def describe_columns(schema, table):
    """
    Loads the description of all columns of the specified table and return their
    description as a dictionary. Each column is identified by its name and
    points to a dictionary containing the information specified in https://www.postgresql.org/docs/9.3/static/infoschema-columns.html:

    * ordinal_position
    * column_default
    * is_nullable
    * data_type
    * character_maximum_length
    * character_octet_length
    * numeric_precision
    * numeric_precision_radix
    * numeric_scale
    * datetime_precision
    * interval_type
    * interval_precision
    * dtd_identifier
    * is_updatable

    :param schema: Schema name

    :param table: Table name

    :return: A dictionary of describing dictionaries representing the columns
    identified by their column names
    """

    engine = _get_engine()
    session = sessionmaker(bind=engine)()
    query = 'select column_name, ' \
            'ordinal_position, column_default, is_nullable, data_type, ' \
            'character_maximum_length, character_octet_length, ' \
            'numeric_precision, numeric_precision_radix, numeric_scale, ' \
            'datetime_precision, interval_type, interval_precision, ' \
            'maximum_cardinality, dtd_identifier, is_updatable ' \
            'from INFORMATION_SCHEMA.COLUMNS where table_name = ' \
            '\'{table}\' and table_schema=\'{schema}\';'.format(
        table=table, schema=schema)
    response = session.execute(query)
    session.close()
    return {column.column_name: {
        'ordinal_position': column.ordinal_position,
        'column_default': column.column_default,
        'is_nullable': column.is_nullable,
        'data_type': column.data_type,
        'character_maximum_length': column.character_maximum_length,
        'character_octet_length': column.character_octet_length,
        'numeric_precision': column.numeric_precision,
        'numeric_precision_radix': column.numeric_precision_radix,
        'numeric_scale': column.numeric_scale,
        'datetime_precision': column.datetime_precision,
        'interval_type': column.interval_type,
        'interval_precision': column.interval_precision,
        'maximum_cardinality': column.maximum_cardinality,
        'dtd_identifier': column.dtd_identifier,
        'is_updatable': column.is_updatable
    } for column in response}


def describe_indexes(schema, table):
    """
    Loads the description of all indexes of the specified table and return their
    description as a dictionary. Each index is identified by its name and
    points to a dictionary containing the following information:

    * indexname: The name of the index
    * indexdef: The SQL-Statement used to create this index

    :param schema: Schema name

    :param table: Table name

    :return: A dictionary of describing dictionaries representing the indexed
    identified by their column names
    """
    engine = _get_engine()
    session = sessionmaker(bind=engine)()
    query = 'select indexname, indexdef from pg_indexes where tablename = ' \
            '\'{table}\' and schemaname=\'{schema}\';'.format(
        table=table, schema=schema)
    print(query)
    response = session.execute(query)
    session.close()

    # Use a single-value dictionary to allow future extension with downward
    # compatibility
    return {column.indexname: {
        'indexdef': column.indexdef,
    } for column in response}


def describe_constraints(schema, table):
    """
    Loads the description of all constraints of the specified table and return their
    description as a dictionary. Each constraints is identified by its name and
    points to a dictionary containing the following information specified in https://www.postgresql.org/docs/9.3/static/infoschema-table-constraints.html:

    * constraint_typ
    * is_deferrable
    * initially_deferred
    * definition: This additional entry contains the SQL-query used to create
        this constraints

    :param schema: Schema name

    :param table: Table name

    :return: A dictionary of describing dictionaries representing the columns
    identified by their column names
    """

    engine = _get_engine()
    session = sessionmaker(bind=engine)()
    query = 'select constraint_name, constraint_type, is_deferrable, initially_deferred, pg_get_constraintdef(c.oid) as definition from information_schema.table_constraints JOIN pg_constraint AS c  ON c.conname=constraint_name where table_name=\'{table}\' AND constraint_schema=\'{schema}\';'.format(
        table=table, schema=schema)
    response = session.execute(query)
    session.close()
    return {column.constraint_name: {
        'constraint_typ': column.constraint_type,
        'is_deferrable': column.is_deferrable,
        'initially_deferred': column.initially_deferred,
        'definition': column.definition
    } for column in response}


def _perform_sql(sql_statement):
    """
    Performs a sql command on standard database.
    :param sql_statement: SQL-Command
    :return: Dictionary with results
    """

    engine = _get_engine()
    session = sessionmaker(bind=engine)()

    # Statement built and no changes required, so statement is empty.
    print("SQL STATEMENT: |" + sql_statement + "|")
    if not sql_statement or sql_statement.isspace():
        return get_response_dict(success=True)

    try:
        result = session.execute(sql_statement)

    except Exception as e:
        print("SQL Action failed. \n Error:\n" + str(e))
        session.rollback()
        return get_response_dict(False, 500, "The sql action could not be finished correctly.", e)

    # Why is commit() not part of close() ?
    # I have to commit the changes before closing session. Otherwise the changes are not persistent.
    session.commit()
    session.close()

    return get_response_dict(success=True, result=result)


def remove_queued_column(id):
    """
    Remove a requested change.
    :param id: id of Change
    :return: Nothing
    """

    sql = "UPDATE api_columns SET reviewed=True WHERE id='{id}'".format(id=id)
    _perform_sql(sql)


def apply_queued_column(id):
    """
    Apply a requested change
    :param id: id of Change
    :return: Result of Database Operation
    """

    column_description = get_column_change(id)
    res = table_change_column(column_description)

    if res.get('success') is True:
        sql = "UPDATE api_columns SET reviewed=True, changed=True WHERE id='{id}'".format(id=id)
    else:
        ex_str = str(res.get('exception'))
        sql = "UPDATE api_columns SET reviewed=False, changed=False, exception={ex_str} WHERE id='{id}'".format(id=id, ex_str=ex_str)

    _perform_sql(sql)
    return res


def apply_queued_constraint(id):
    """
    Apply a requested change to constraints
    :param id: id of Change
    :return: Result of Database Operation
    """

    constraint_description = get_constraint_change(id)
    res = table_change_constraint(constraint_description)

    if res.get('success') is True:
        sql = "UPDATE api_constraints SET reviewed=True, changed=True WHERE id='{id}'".format(id=id)
    else:
        ex_str = str(res.get('exception'))
        sql = "UPDATE api_constraints SET reviewed=False, changed=False, exception={ex_str} WHERE id='{id}'".format(id=id, ex_str=ex_str)
    _perform_sql(sql)
    return res


def remove_queued_constraint(id):
    """
    Remove a requested change to constraints
    :param id:
    :return:
    """

    sql = "UPDATE api_constraints SET reviewed=True WHERE id='{id}'".format(id=id)
    _perform_sql(sql)


def get_response_dict(success, http_status_code=200, reason=None, exception=None, result=None):
    """
    Unified error description
    :param success: Task was successful or unsuccessful
    :param http_status_code: HTTP status code for indication
    :param reason: reason, why task failed, humanreadable
    :param exception exception, if available
    :return: Dictionary with results
    """
    dict = {'success': success,
            'error': str(reason).replace('\n', ' ').replace('\r', ' ') if reason is not None else None,
            'http_status': http_status_code,
            'exception': exception,
            'result': result
            }
    return dict


def queue_constraint_change(schema, table, constraint_def):
    """
    Queue a change to a constraint
    :param schema: Schema
    :param table: Table
    :param constraint_def: Dict with constraint definition
    :return: Result of database command
    """

    cd = api.parser.replace_None_with_NULL(constraint_def)

    sql_string = "INSERT INTO public.api_constraints (action, constraint_type" \
                 ", constraint_name, constraint_parameter, reference_table, reference_column, c_schema, c_table) " \
                 "VALUES ('{action}', '{c_type}', '{c_name}', '{c_parameter}', '{r_table}', '{r_column}' , '{c_schema}' " \
                 ", '{c_table}');".format(action=cd['action'], c_type=cd['constraint_type'],
                                          c_name=cd['constraint_name'], c_parameter=cd['constraint_parameter'],
                                          r_table=cd['reference_table'], r_column=cd['reference_column'],
                                          c_schema=schema, c_table=table).replace('\'NULL\'', 'NULL')

    return _perform_sql(sql_string)


def queue_column_change(schema, table, column_definition):
    """
    Quere a change to a column
    :param schema: Schema
    :param table: Table
    :param column_definition: Dict with column definition
    :return: Result of database command
    """

    column_definition = api.parser.replace_None_with_NULL(column_definition)

    sql_string = "INSERT INTO public.api_columns (column_name, not_null, data_type, new_name, c_schema, c_table) " \
                 "VALUES ('{name}','{not_null}','{data_type}','{new_name}','{c_schema}','{c_table}');" \
        .format(name=column_definition['column_name'], not_null=column_definition['not_null'],
                data_type=column_definition['data_type'], new_name=column_definition['new_name'], c_schema=schema,
                c_table=table) \
        .replace('\'NULL\'', 'NULL')

    return _perform_sql(sql_string)


def get_column_change(i_id):
    """
    Get one explicit change
    :param i_id: ID of Change
    :return: Change or None, if no change found
    """
    all_changes = get_column_changes()
    for change in all_changes:
        print(change.get('id'))
        if int(change.get('id')) == int(i_id):
            return change

    return None


def get_constraint_change(i_id):
    """
    Get one explicit change
    :param i_id: ID of Change
    :return: Change or None, if no change found
    """
    all_changes = get_constraints_changes()

    for change in all_changes:
        if int(change.get('id')) == int(i_id):
            return change

    return None


def get_column_changes(reviewed=None, changed=None, schema=None, table=None):
    """
    Get all column changes
    :param reviewed: Reviewed Changes
    :param changed: Applied Changes
    :return: List with Column Definitions
    """

    engine = _get_engine()
    session = sessionmaker(bind=engine)()
    query = ["SELECT * FROM public.api_columns"]

    if reviewed is not None or changed is not None or schema is not None or table is not None:
        query.append(" WHERE ")

        where = []

        if reviewed is not None:
            where.append("reviewed = " + str(reviewed))

        if changed is not None:
            where.append("changed = " + str(changed))

        if schema is not None:
            where.append("c_schema = '{schema}'".format(schema=schema))

        if table is not None:
            where.append("c_table = '{table}'".format(table=table))

        query.append(" AND ".join(where))

    query.append(";")

    sql = ''.join(query)

    print(sql)
    response = session.execute(sql)
    session.close()

    return [{'column_name': column.column_name,
             'not_null': column.not_null,
             'data_type': column.data_type,
             'new_name': column.new_name,
             'reviewed': column.reviewed,
             'changed': column.changed,
             'c_schema': column.c_schema,
             'c_table': column.c_table,
             'id': column.id,
             'exception': column.exception
             } for column in response]


def get_constraints_changes(reviewed=None, changed=None, schema=None, table=None):
    """
    Get all constraint changes
    :param reviewed: Reviewed Changes
    :param changed: Applied Changes
    :return: List with Column Definitons
    """
    engine = _get_engine()
    session = sessionmaker(bind=engine)()
    query = ["SELECT * FROM public.api_constraints"]

    if reviewed is not None or changed is not None or schema is not None or table is not None:
        query.append(" WHERE ")

        where = []

        if reviewed is not None:
            where.append("reviewed = " + str(reviewed))

        if changed is not None:
            where.append("changed = " + str(changed))

        if schema is not None:
            where.append("c_schema = '{schema}'".format(schema=schema))

        if table is not None:
            where.append("c_table = '{table}'".format(table=table))

        query.append(" AND ".join(where))

    query.append(";")

    sql = ''.join(query)

    print(sql)
    response = session.execute(sql)
    session.close()

    return [{'action': column.action,
             'constraint_type': column.constraint_type,
             'constraint_name': column.constraint_name,
             'constraint_parameter': column.constraint_parameter,
             'reference_table': column.reference_table,
             'reference_column': column.reference_column,
             'reviewed': column.reviewed,
             'changed': column.changed,
             'c_schema': column.c_schema,
             'c_table': column.c_table,
             'id': column.id,
             'exception': column.exception
             } for column in response]


def table_create(schema, table, columns, constraints):
    """
    Creates a new table.
    :param schema: schema
    :param table: table
    :param columns: Description of columns
    :param constraints: Description of constraints
    :return: Dictionary with results
    """

    # Building and joining a string array seems to be more efficient than native string concats.
    # https://waymoot.org/home/python_string/

    str_list = []
    str_list.append("CREATE TABLE {schema}.\"{table}\" (".format(schema=schema, table=table))

    print("Columns: " + str(columns))
    print("Constraints: " + str(constraints))

    first_column = True
    for c in columns:
        if not first_column:
            str_list.append(",")
        str_list.append("{name} {data_type} {not_null}"
                        .format(name=c['name'], data_type=c['data_type'],
                                not_null="NOT NULL" if "NO" in c['is_nullable'] else ""))
        first_column = False

    str_list.append(");")
    sql_string = ''.join(str_list)

    print("SQL CREATE String: " + sql_string)

    results = [_perform_sql(sql_string)]

    for constraint_definition in constraints:
        print("ConDef in CREATE TABLE: " + str(constraint_definition))
        results.append(table_change_constraint(constraint_definition))

    for res in results:
        if not res['success']:
            return res

    return get_response_dict(success=True)

def table_change_column(column_definition):
    """
    Changes a table column.
    :param schema: schema
    :param table: table
    :param column_definition: column definition according to Issue #184
    :return: Dictionary with results
    """

    schema = column_definition['c_schema']
    table = column_definition['c_table']

    # Check if column exists
    existing_column_description = describe_columns(schema, table)

    if len(existing_column_description) <= 0:
        return get_response_dict(False, 400, 'table is not defined.')

    # There is a table named schema.table.
    sql = []

    start_name = column_definition['column_name']
    current_name = column_definition['column_name']

    if column_definition['column_name'] in existing_column_description:
        # Column exists and want to be changed

        # Figure out, which column should be changed and constraint or datatype or name should be changed

        if column_definition['new_name'] is not None:
            # Rename table
            sql.append(
                "ALTER TABLE {schema}.{table} RENAME COLUMN {name} TO {new_name};".format(schema=schema, table=table,
                                                                                          name=column_definition[
                                                                                              'column_name'],
                                                                                          new_name=column_definition[
                                                                                              'new_name']))
            # All other operations should work with new name
            current_name = column_definition['new_name']

        cdef_datatype = column_definition.get('data_type')
        # TODO: Fix rudimentary handling of datatypes
        if cdef_datatype is not None and cdef_datatype != existing_column_description[column_definition['name']][
            'data_type']:
            sql.append("ALTER TABLE {schema}.{table} ALTER COLUMN {c_name} TYPE {c_datatype};".format(schema=schema,
                                                                                                      table=table,
                                                                                                      c_name=current_name,
                                                                                                      c_datatype=
                                                                                                      column_definition[
                                                                                                          'data_type']))

        c_null = 'NO' in existing_column_description[start_name]['is_nullable']
        cdef_null = column_definition.get('not_null');
        if cdef_null is not None and c_null != cdef_null:
            if c_null:
                # Change to nullable
                sql.append('ALTER TABLE {schema}.{table} ALTER COLUMN {c_name} DROP NOT NULL;'.format(schema=schema,
                                                                                                      table=table,
                                                                                                      c_name=current_name))
            else:
                # Change to not null
                sql.append('ALTER TABLE {schema}.{table} ALTER COLUMN {c_name} SET NOT NULL;'.format(schema=schema,
                                                                                                     table=table,
                                                                                                     c_name=current_name))
    else:
        # Column does not exist and should be created
        # Request will end in 500, if an argument is missing.
        sql.append(
            "ALTER TABLE {schema}.{table} ADD {c_name} {c_datatype} {c_notnull};".format(schema=schema, table=table,
                                                                                         c_name=current_name,
                                                                                         c_datatype=column_definition[
                                                                                             'data_type'],
                                                                                         c_notnull="NOT NULL" if
                                                                                         column_definition[
                                                                                             'notnull'] else ""))

    sql_string = ''.join(sql)

    return _perform_sql(sql_string)


def table_change_constraint(constraint_definition):
    """
    Changes constraint of table
    :param schema: schema
    :param table: table
    :param constraint_definition: constraint definition according to Issue #184
    :return: Dictionary with results
    """

    table = constraint_definition['c_table']
    schema = constraint_definition['c_schema']

    existing_column_description = describe_columns(schema, table)

    if len(existing_column_description) <= 0:
        return {'success': False,
                'error': 'Table does not exists.'}

    # There is a table named schema.table.
    sql = []

    if 'ADD' in constraint_definition['action']:
        sql.append(
            'ALTER TABLE {schema}.{table} {action} CONSTRAINT {constraint_name} {constraint_type} ({constraint_parameter})'.format(
                schema=schema, table=table, action=constraint_definition['action'],
                constraint_name=constraint_definition['constraint_name'],
                constraint_parameter=constraint_definition['constraint_parameter'],
                constraint_type=constraint_definition['constraint_type']))

        if 'FOREIGN KEY' in constraint_definition['constraint_type']:
            if constraint_definition['reference_table'] is None or constraint_definition['reference_column'] is None:
                return get_response_dict(False, 400, 'references are not defined correctly')
            sql.append(' REFERENCES {reference_table}({reference_column})'.format(
                reference_column=constraint_definition['reference_column'],
                reference_table=constraint_definition['reference_table']))

        sql.append(';')
    elif 'DROP' in constraint_definition['action']:
        sql.append('ALTER TABLE {schema}.{table} DROP CONSTRAINT {constraint_name}'.format(schema=schema, table=table,
                                                                                           constraint_name=
                                                                                           constraint_definition[
                                                                                               'constraint_name']))

    sql_string = ''.join(sql)

    print(sql_string)
    return _perform_sql(sql_string)


def get_rows(request, data):

    sql = ['SELECT']
    columns = data.get('columns')
    if columns is None:
        sql.append('*')
    else:
        sql.append(','.join(columns))

    sql.append('FROM {schema}.{table}'.format(schema=data['schema'], table=data['table']))

    where = data.get('where')
    if where is not None:
        sql.append('WHERE')

        for i in range(0, int(len(where)/2)):
            first = where[2 * i]
            second = where[2 * i + 1]

            if i != 0:
                # TODO: Add Support for OR Connections
                sql.append('AND')

            if not second.isdigit():
                second = "'" + second + "'"

            sql.append(first + '=' + second)

    orderby = data.get('orderby')
    if orderby is not None:
        sql.append('ORDER BY')
        sql.append(','.join(orderby))

    limit = data.get('limit')
    if limit is not None and limit.isdigit():
        sql.append('LIMIT ' + limit)

    offset = data.get('offset')
    if offset is not None and offset.isdigit():
        sql.append('OFFSET ' + offset)

    sql_command = ' '.join(sql)
    print(sql_command)

    resp_dict = _perform_sql(sql_command)
    result = resp_dict.get('result')

    if result is None:
        # Returning an empty list is equivalent to returning an empty result.
        return []

    return [dict(r) for r in result]

"""
ACTIONS FROM OLD API
"""


def _get_table(schema, table):
    engine = _get_engine()
    metadata = MetaData()

    return Table(table, metadata, autoload=True, autoload_with=engine, schema=schema)


"""


def table_create(request, context=None):
    # TODO: Authentication
    # TODO: column constrains: Unique,
    # TODO: column constrains: Unique,
    # load schema name and check for sanity
    engine = _get_engine()

    schema = read_pgid(request["schema"])
    create_schema = not has_schema(request)
    # Check whether schema exists

    # load table name and check for sanity
    table = read_pgid(request.pop("table"))

    # Process fields
    fieldstrings = []
    fields = request.pop("fields", [])
    foreign_keys = []
    primary_keys = []
    for field in fields:
        fname = read_pgid(field["name"])
        type_name = field["type"]

        # TODO: check whether type_name is an actual postgres type
        # if not engine.dialect.has_type(connection,type_name):
        #    raise p.toolkit.ValidationError("Invalid field type: '%s'"% type_name )
        fs = field["name"] + " " + type_name

        if "pk" in field:
            if read_bool(field["pk"]):
                primary_keys.append([field["name"]])
                fs += " PRIMARY KEY"

        fieldstrings.append(fs)

    table_constraints = {"unique": [], "pk": primary_keys, "fk": foreign_keys}
    constraints = request.pop('constraints', {})
    if 'fk' in constraints:
        assert isinstance(constraints['fk'], list), \
            "Foreign Keys should be a list"
        for fk in constraints['fk']:
            print(fk)
            assert all(map(is_pg_qual, [fk["schema"], fk["table"]] + fk["fields"] + fk["names"])), "Invalid identifier"
            if 'on_delete' in fk:
                assert fk["on delete"].lower() in ["cascade", "no action",
                                                   "restrict", "set null",
                                                   "set default"], "Invalid on delete action"
            else:
                fk["on_delete"] = "no action"
            foreign_keys.append((fk["names"],
                                 fk["schema"],
                                 fk["table"],
                                 fk["fields"],
                                 fk["on_delete"]))

    #fieldstrings.append("_comment int")


    #foreign_keys.append(("_comment", schema, "_"+table+"_cor", "id", "no action"))
    fk_constraints = []
    for (
            fk_field1, fk_schema, fk_table, fk_field2,
            fk_on_delete) in foreign_keys:
        fk_constraints.append(
            "FOREIGN KEY ({field1}) references {schema}.{table} ({field2}) match simple on update no action on delete {ondel}".format(
                field1=",".join(fk_field1), schema=fk_schema, table=fk_table,
                field2=",".join(fk_field2), ondel=fk_on_delete)
        )
    constraints = ", ".join(fk_constraints)
    fields = "(" + (
        ", ".join(fieldstrings + fk_constraints) if fieldstrings else "") + ")"
    sql_string = "create table {schema}.{table} {fields}".format(
        schema=schema, table=table, fields=fields, constraints=constraints)
    print(fk_constraints)
    session = sessionmaker(bind=engine)()
    try:
        if create_schema:
            session.execute("create schema %s" % schema)

        session.execute(sql_string.replace('%', '%%'))
        #create_meta(schema, table)
    except Exception as e:
        traceback.print_exc()
        session.rollback()
        raise e
    else:
        session.commit()
    return {'success': True}

"""


def data_delete(request, context=None):
    raise NotImplementedError()


def data_update(request, context=None):
    engine = _get_engine()
    connection = engine.connect()
    query = {
        'from': [{
            'type': 'table',
            'schema': request['schema'],
            'table': request['table']
        }],
        'where': request['where']
    }
    user = context['user'].name
    rows = data_search(query, context)
    setter = request['values']
    message = request.get('message', None)
    meta_fields = list(parser.set_meta_info('update', user, message).items())
    fields = [field[0] for field in rows['description']] + [f[0] for f in meta_fields]

    table_name = request['table']
    meta = MetaData(bind=engine)
    table = Table(table_name, meta, autoload=True, schema=request['schema'])
    pks = [c for c in table.columns if c.primary_key]

    insert_strings = []
    if rows['data']:
        for row in rows['data']:
            insert = []
            for (key, value) in list(zip(fields, row)) + meta_fields:
                if key in setter:
                    if not (key in pks and value != setter[key]):
                        value = setter[key]
                    else:
                        raise InvalidRequest(
                            "Primary keys must remain unchanged.")
                insert.append(process_value(value))

            insert_strings.append('(' + (', '.join(insert)) + ')')

        # Add metadata for insertions
        schema = request['schema']
        schema = get_meta_schema_name(schema) if not schema.startswith('_') else schema

        s = "INSERT INTO {schema}.{table} ({fields}) VALUES {values}".format(
            schema=api.parser.read_pgid(schema),
            table=api.parser.read_pgid(get_edit_table_name(table_name)),
            fields=', '.join(fields),
            values=', '.join(insert_strings)
        )
        print(s)
        connection.execute(s)
    return {'affected': len(rows['data'])}


def data_insert(request, context=None):
    print("INSERT: ", request)
    engine = _get_engine()
    connection = engine.connect()
    query = request

    # If the insert request is not for a meta table, change the request to do so
    assert not query['table'].startswith('_') or query['table'].endswith(
        '_cor'), "Insertions on meta tables are only allowed on comment tables"
    query['table'] = '_' + query['table'] + '_insert'
    if not query['schema'].startswith('_'):
        query['schema'] = '_' + query['schema']

    query = parser.parse_insert(request, engine, context)
    print(query, query.__dict__)
    result = connection.execute(query)
    connection.close()
    description = result.context.cursor.description
    if not result.returns_rows:
        return {}

    data = [list(r) for r in result]
    return {'data': data,
            'description': [[col.name, col.type_code, col.display_size,
                             col.internal_size, col.precision, col.scale,
                             col.null_ok] for col in description]}


def process_value(val):
    if isinstance(val, str):
        return "'" + val + "'"
    if isinstance(val, datetime):
        return "'" + str(val) + "'"
    if val is None:
        return 'null'
    else:
        return str(val)


def table_drop(request, context=None):
    db = request["db"]
    engine = _get_engine()
    connection = engine.connect()

    # load schema name and check for sanity    
    schema = request.pop("schema", "public")
    if not api.parser.is_pg_qual(schema):
        return {'success': False, 'reason': 'Invalid schema name: %s' % schema}
        # Check whether schema exists

    # load table name and check for sanity
    table = request.pop("table", None)

    if not api.parser.is_pg_qual(table):
        return {'success': False, 'reason': 'Invalid table name: %s' % table}

    try:
        exists = bool(request.pop("exists", False))
    except:
        return {'success': False,
                'reason': 'Invalid exists clause: %s' % exists}

    option = request.pop("option", None)
    if option and option.lower() not in ["cascade", "restrict"]:
        return {'success': False, 'reason': 'Invalid option clause name: %s' % option}

    sql_string = "drop table {exists} {schema}.{table} {option} ".format(
        schema=schema,
        table=table,
        option=option if option else "",
        exists="IF EXISTS" if exists else "")

    session = sessionmaker(bind=engine)()
    try:
        session.execute(sql_string.replace('%', '%%'))
    except Exception as e:
        traceback.print_exc()
        session.rollback()
        raise e
    else:
        session.commit()

    return {}


def data_search(request, context=None):
    engine = _get_engine()
    connection = engine.connect()
    query = parser.parse_select(request)
    print(query)
    result = connection.execute(query)
    description = result.context.cursor.description
    data = [list(r) for r in result]
    return {'data': data,
            'description': [[col.name, col.type_code, col.display_size,
                             col.internal_size, col.precision, col.scale,
                             col.null_ok] for col in description]}


def _get_count(q):
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    count = q.session.execute(count_q).scalar()
    return count


def count_all(request, context=None):
    table = request['table']
    schema = request['schema']
    engine = _get_engine()
    session = sessionmaker(bind=engine)()
    t = _get_table(schema, table)
    return session.query(t).count()  # _get_count(session.query(t))


def _get_header(results):
    header = []
    for field in results.cursor.description:
        header.append({
            'id': field[0],  # .decode('utf-8'),
            'type': field[1]
        })
    return header


def analyze_columns(db, schema, table):
    engine = _get_engine()
    connection = engine.connect()
    result = connection.execute(
        "select column_name as id, data_type as type from information_schema.columns where table_name = '{table}' and table_schema='{schema}';".format(
            schema=schema, table=table))
    return [{'id': r['id'], 'type': r['type']} for r in result]


def search(db, schema, table, fields=None, pk=None, offset=0, limit=100):
    if not fields:
        fields = '*'
    else:
        fields = ', '.join(fields)
    engine = _get_engine()
    connection = engine.connect()
    refs = connection.execute(references.Entry.__table__.select())

    sql_string = "select {fields} from {schema}.{table}".format(
        schema=schema, table=table, fields=fields)

    if pk:
        sql_string += " where {} = {}".format(pk[0], pk[1])

    sql_string += " limit {}".format(limit)
    sql_string += " offset {}".format(offset)
    return connection.execute(sql_string, ), [dict(refs.first()).items()]


def clear_dict(d):
    return {
        k.replace(" ", "_"): d[k] if not isinstance(d[k], dict) else clear_dict(
            d[k]) for k in d}


def create_meta(schema, table):
    meta_schema = get_meta_schema_name(schema)

    if not has_schema({'schema': '_' + schema}):
        create_meta_schema(schema)

    # Comment table
    if not has_table(
            {'schema': meta_schema,
             'table': get_comment_table_name(table)}):
        create_comment_table(schema, table)

    # Table for updates
    if not has_table(
            {'schema': meta_schema,
             'table': get_edit_table_name(table)}):
        create_edit_table(schema, table)

    # Table for inserts
    if not has_table(
            {'schema': meta_schema,
             'table': get_insert_table_name(table)}):
        create_insert_table(schema, table)

    table = get_comment_table_name(table)
    # Table for updates on comments
    if not has_table(
            {'schema': meta_schema,
             'table': get_edit_table_name(table)}):
        create_edit_table(meta_schema, table, meta_schema=meta_schema)

    # Table for inserts on comments
    if not has_table(
            {'schema': meta_schema,
             'table': get_insert_table_name(table)}):
        create_insert_table(meta_schema, table, meta_schema=meta_schema)


def get_comment_table(db, schema, table):
    engine = _get_engine()
    connection = engine.connect()

    sql_string = "select obj_description('{schema}.{table}'::regclass::oid, 'pg_class');".format(
        schema=schema, table=table)

    res = connection.execute(sql_string)
    if res:
        jsn = res.first().obj_description
        if jsn:
            jsn = jsn.replace('\n', '')
        else:
            return {}
        try:
            return json.loads(jsn)
        except ValueError:
            return {'error': 'No json format', 'content': jsn}
    else:
        return {}


"""
def data_insert(request):
    engine = _get_engine()
    # load schema name and check for sanity    
    schema = request["schema"]

    if not is_pg_qual(schema):
        raise parser.ValidationError("Invalid schema name")
        # Check whether schema exists

    # load table name and check for sanity
    table = request.pop("table", None)
    if not is_pg_qual(table):
        raise parser.ValidationError("Invalid table name")

    fields = request.pop("fields", "*")
    if fields != "*" and not all(map(is_pg_qual, fields)):
        raise parser.ValidationError("Invalid field name")
    fieldsstring = "(" + (", ".join(fields)) + ")" if fields != "*" else ""

    if bool(request.pop("default", False)):
        data = " DEFAULT VALUES"
    else:
        data = request.pop("values", [])

    returning = request.pop("returning", '')
    if returning:
        returning = 'returning ' + ', '.join(map(parser.parse_expression, returning))

    connection = engine.connect()

    result = connection.execute(
        "INSERT INTO {schema}.{table} {fields} VALUES{markers} {returning}".format(
            schema=schema, table=table, fields=fieldsstring,
            markers="(" + (",".join("%s" for i in range(len(data[0])))) + ")",
            returning=returning),
        data)
    if returning:
        description = result.context.cursor.description
        data = [list(r) for r in result]
        return {'data': data,
                'description': [[col.name, col.type_code, col.display_size,
                                 col.internal_size, col.precision, col.scale,
                                 col.null_ok] for col in description]}
    else:
        return request
"""


def data_info(request, context=None):
    return request


def connect():
    engine = _get_engine()
    insp = sqla.inspect(engine)
    return insp


def _get_engine():
    engine = sqla.create_engine(
        'postgresql://{0}:{1}@{2}:{3}/{4}'.format(
            sec.dbuser,
            sec.dbpasswd,
            sec.dbhost,
            sec.dbport,
            sec.dbname))
    return engine


def has_schema(request, context=None):
    engine = _get_engine()
    result = engine.dialect.has_schema(engine.connect(), request['schema'])
    return result


def has_table(request, context=None):
    engine = _get_engine()
    schema = request.pop('schema', None)
    table = request['table']
    result = engine.dialect.has_table(engine.connect(), table,
                                      schema=schema)
    return result


def has_sequence(request, context=None):
    engine = _get_engine()
    result = engine.dialect.has_sequence(engine.connect(),
                                         request['sequence_name'],
                                         schema=request.pop('schema', None))
    return result


def has_type(request, context=None):
    engine = _get_engine()
    result = engine.dialect.has_schema(engine.connect(),
                                       request['sequence_name'],
                                       schema=request.pop('schema', None))
    return result


def get_table_oid(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_table_oid(engine.connect(),
                                          request['table'],
                                          schema=request['schema'],
                                          **request)
    return result


def get_schema_names(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_schema_names(engine.connect(), **request)
    return result


def get_table_names(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_table_names(engine.connect(),
                                            schema=request.pop('schema',
                                                               None),
                                            **request)
    return result


def get_view_names(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_view_names(engine.connect(),
                                           schema=request.pop('schema', None),
                                           **request)
    return result


def get_view_definition(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_schema_names(engine.connect(),
                                             request['view_name'],
                                             schema=request.pop('schema',
                                                                None),
                                             **request)
    return result


def get_columns(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_columns(engine.connect(),
                                        request['table'],
                                        schema=request.pop('schema', None),
                                        **request)
    return result


def get_pk_constraint(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_pk_constraint(engine.connect(),
                                              request['table'],
                                              schema=request.pop('schema',
                                                                 None),
                                              **request)
    return result


def get_foreign_keys(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_foreign_keys(engine.connect(),
                                             request['table'],
                                             schema=request.pop('schema',
                                                                None),
                                             postgresql_ignore_search_path=request.pop(
                                                 'postgresql_ignore_search_path',
                                                 False),
                                             **request)
    return result


def get_indexes(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_indexes(engine.connect(),
                                        request['table'],
                                        request['schema'],
                                        **request)
    return result


def get_unique_constraints(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_foreign_keys(engine.connect(),
                                             request['table'],
                                             schema=request.pop('schema',
                                                                None),
                                             **request)
    return result


def get_comment_table_name(table):
    return '_' + table + '_cor'


def get_edit_table_name(table):
    return '_' + table + '_edit'


def get_insert_table_name(table):
    return '_' + table + '_insert'


def get_meta_schema_name(schema):
    return '_' + schema


def create_meta_schema(schema):
    engine = _get_engine()
    query = 'CREATE SCHEMA {schema}'.format(schema=get_meta_schema_name(schema))
    connection = engine.connect()
    connection.execute(query)


def create_edit_table(schema, table, meta_schema=None):
    if not meta_schema:
        meta_schema = get_meta_schema_name(schema)
    engine = _get_engine()
    query = 'CREATE TABLE {meta_schema}.{edit_table} ' \
            '(LIKE {schema}.{table} INCLUDING ALL EXCLUDING INDEXES, PRIMARY KEY (_id)) ' \
            'INHERITS (_edit_base);'.format(
        meta_schema=meta_schema,
        edit_table=get_edit_table_name(table),
        schema=schema,
        table=table)
    print(query)
    connection = engine.connect()
    connection.execute(query)


def create_insert_table(schema, table, meta_schema=None):
    if not meta_schema:
        meta_schema = get_meta_schema_name(schema)
    engine = _get_engine()
    query = 'CREATE TABLE {meta_schema}.{edit_table} () ' \
            'INHERITS (_insert_base, {schema}.{table});'.format(
        meta_schema=meta_schema,
        edit_table=get_insert_table_name(table),
        schema=schema,
        table=table)
    print(query)
    connection = engine.connect()
    connection.execute(query)


def create_comment_table(schema, table, meta_schema=None):
    if not meta_schema:
        meta_schema = get_meta_schema_name(schema)
    engine = _get_engine()
    query = 'CREATE TABLE {schema}.{table} (PRIMARY KEY (_id)) ' \
            'INHERITS (_comment_base); '.format(
        schema=meta_schema,
        table=get_comment_table_name(table))
    connection = engine.connect()
    connection.execute(query)
