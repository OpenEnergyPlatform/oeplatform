import itertools
import json
import logging
import re
import traceback
from datetime import datetime

import geoalchemy2  # Although this import seems unused is has to be here
import psycopg2
import sqlalchemy as sa
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from omi.dialects.oep.parser import JSONParser_1_4, ParserException
from shapely import wkb, wkt
from sqlalchemy import Column, ForeignKey, MetaData, Table, exc, func, sql
from sqlalchemy import types as sqltypes
from sqlalchemy import util
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql import column
from sqlalchemy.sql.expression import func
from omi.dialects.oep import OEP_V_1_4_Dialect as OmiDialect
import api
import login.models as login_models
from api import DEFAULT_SCHEMA, references
from api.connection import _get_engine
from api.error import APIError
from api.parser import get_or_403, read_bool, read_pgid, parse_type
from api.sessions import (
    SessionContext,
    close_all_for_user,
    load_cursor_from_context,
    load_session_from_context,
)
from dataedit.models import Table as DBTable
from dataedit.structures import MetaSearch
from oeplatform.securitysettings import PLAYGROUNDS, UNVERSIONED_SCHEMAS

pgsql_qualifier = re.compile(r"^[\w\d_\.]+$")


logger = logging.getLogger("oeplatform")

__INSERT = 0
__UPDATE = 1
__DELETE = 2


def get_column_obj(table, column):
    """

    :param talbe: A sqla-table object
    :param column: A column name
    :return: Basically `getattr(table.c, column)` but throws an exception of the
        column does not exists
    """
    tc = table.c
    try:
        return getattr(tc, column)
    except AttributeError:
        raise APIError("Column '%s' does not exist." % column)


def get_table_name(schema, table, restrict_schemas=True):
    if not has_schema(dict(schema=schema)):
        raise Http404
    if not has_table(dict(schema=schema, table=table)):
        raise Http404
    if schema.startswith("_") or schema == "public" or schema is None:
        raise PermissionDenied
    if restrict_schemas:
        if schema not in PLAYGROUNDS + UNVERSIONED_SCHEMAS:
            raise PermissionDenied
    return schema, table


Base = declarative_base()


class ResponsiveException(Exception):
    pass


def assert_permission(user, table, permission, schema=None):
    if schema is None:
        schema = DEFAULT_SCHEMA
    if (
        user.is_anonymous
        or user.get_table_permission_level(DBTable.load(schema, table)) < permission
    ):
        raise PermissionDenied


def _translate_fetched_cell(cell):
    if isinstance(cell, geoalchemy2.WKBElement):
        return _get_engine().execute(cell.ST_AsText()).scalar()
    elif isinstance(cell, memoryview):
        return wkb.dumps(wkb.loads(cell.tobytes()), hex=True)
    else:
        return cell


def __response_success():
    return {"success": True}


def _response_error(message):
    return {"success": False, "message": message}


class InvalidRequest(Exception):
    pass


def _translate_sqla_type(column):
    if column.data_type.lower() == "array":
        return column.element_type + "[]"
    if column.data_type.lower() == "user-defined":
        return column.udt_name
    else:
        return column.data_type

def try_parse_metadata(inp):
    """
    :param inp: string or dict
    :return: Tuple[OEPMetadata or None, string or None]:
        The first component is the result of the parsing procedure or `None` if
        the parsing failed. The second component is None, if the parsing failed,
        otherwise an error message.

    .. doctest::

        >>> from api.actions import try_parse_metadata
        >>> result, error = try_parse_metadata('{"id":"id"}')
        >>> error is None
        True

    """

    parser = JSONParser_1_4()
    if isinstance(inp, dict):
        jsn = inp
    else:
        try:
            jsn = json.loads(inp)
        except:
            return None, "Could not parse json"
    try:
        metadata = parser.parse(jsn)
    except ParserException as e:
        return None, str(e)
    except:
        raise APIError("Metadata could not be parsed")
    else:
        return metadata, None


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
    query = (
        "select column_name, "
        "c.ordinal_position, c.column_default, c.is_nullable, c.data_type, "
        "c.character_maximum_length, c.character_octet_length, "
        "c.numeric_precision, c.numeric_precision_radix, c.numeric_scale, "
        "c.datetime_precision, c.interval_type, c.interval_precision, "
        "c.maximum_cardinality, c.dtd_identifier, c.udt_name, c.is_updatable, e.data_type as element_type "
        "from INFORMATION_SCHEMA.COLUMNS  c "
        "LEFT JOIN information_schema.element_types e "
        "ON ((c.table_catalog, c.table_schema, c.table_name, 'TABLE', c.dtd_identifier) "
        "= (e.object_catalog, e.object_schema, e.object_name, e.object_type, e.collection_type_identifier)) where table_name = "
        "'{table}' and table_schema='{schema}';".format(table=table, schema=schema)
    )
    response = session.execute(query)
    session.close()
    return {
        column.column_name: {
            "ordinal_position": column.ordinal_position,
            "column_default": column.column_default,
            "is_nullable": column.is_nullable == "YES",
            "data_type": _translate_sqla_type(column),
            "character_maximum_length": column.character_maximum_length,
            "character_octet_length": column.character_octet_length,
            "numeric_precision": column.numeric_precision,
            "numeric_precision_radix": column.numeric_precision_radix,
            "numeric_scale": column.numeric_scale,
            "datetime_precision": column.datetime_precision,
            "interval_type": column.interval_type,
            "interval_precision": column.interval_precision,
            "maximum_cardinality": column.maximum_cardinality,
            "dtd_identifier": column.dtd_identifier,
            "is_updatable": column.is_updatable == "YES",
        }
        for column in response
    }


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
    query = (
        "select indexname, indexdef from pg_indexes where tablename = "
        "'{table}' and schemaname='{schema}';".format(table=table, schema=schema)
    )
    response = session.execute(query)
    session.close()

    # Use a single-value dictionary to allow future extension with downward
    # compatibility
    return {column.indexname: {"indexdef": column.indexdef} for column in response}


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
    query = "select constraint_name, constraint_type, is_deferrable, initially_deferred, pg_get_constraintdef(c.oid) as definition from information_schema.table_constraints JOIN pg_constraint AS c  ON c.conname=constraint_name where table_name='{table}' AND constraint_schema='{schema}';".format(
        table=table, schema=schema
    )
    response = session.execute(query)
    session.close()
    return {
        column.constraint_name: {
            "constraint_type": column.constraint_type,
            "is_deferrable": column.is_deferrable,
            "initially_deferred": column.initially_deferred,
            "definition": column.definition,
        }
        for column in response
    }


def perform_sql(sql_statement, parameter=None):
    """
    Performs a sql command on standard database.
    :param sql_statement: SQL-Command
    :return: Dictionary with results
    """

    if not parameter:
        parameter = {}

    engine = _get_engine()
    session = sessionmaker(bind=engine)()

    # Statement built and no changes required, so statement is empty.
    if not sql_statement or sql_statement.isspace():
        return get_response_dict(success=True)

    try:
        result = session.execute(sql_statement, parameter)
    except Exception as e:
        print("SQL Action failed. \n Error:\n" + str(e))
        session.rollback()
        raise APIError(str(e))
    else:
        # Why is commit() not part of close() ?
        # I have to commit the changes before closing session. Otherwise the changes are not persistent.
        session.commit()
    finally:
        session.close()

    return get_response_dict(success=True, result=result)


def remove_queued_column(id):
    """
    Remove a requested change.
    :param id: id of Change
    :return: Nothing
    """

    sql = "UPDATE api_columns SET reviewed=True WHERE id='{id}'".format(id=id)
    perform_sql(sql)


def apply_queued_column(id):
    """
    Apply a requested change
    :param id: id of Change
    :return: Result of Database Operation
    """

    column_description = get_column_change(id)
    res = table_change_column(column_description)

    if res.get("success") is True:
        sql = "UPDATE api_columns SET reviewed=True, changed=True WHERE id='{id}'".format(
            id=id
        )
    else:
        ex_str = str(res.get("exception"))
        sql = "UPDATE api_columns SET reviewed=False, changed=False, exception={ex_str} WHERE id='{id}'".format(
            id=id, ex_str=ex_str
        )

    perform_sql(sql)
    return res


def apply_queued_constraint(id):
    """
    Apply a requested change to constraints
    :param id: id of Change
    :return: Result of Database Operation
    """

    constraint_description = get_constraint_change(id)
    res = table_change_constraint(constraint_description)

    if res.get("success") is True:
        sql = "UPDATE api_constraints SET reviewed=True, changed=True WHERE id='{id}'".format(
            id=id
        )
    else:
        ex_str = str(res.get("exception"))
        sql = "UPDATE api_constraints SET reviewed=False, changed=False, exception={ex_str} WHERE id='{id}'".format(
            id=id, ex_str=ex_str
        )
    perform_sql(sql)
    return res


def remove_queued_constraint(id):
    """
    Remove a requested change to constraints
    :param id:
    :return:
    """

    sql = "UPDATE api_constraints SET reviewed=True WHERE id='{id}'".format(id=id)
    perform_sql(sql)


def get_response_dict(
    success, http_status_code=200, reason=None, exception=None, result=None
):
    """
    Unified error description
    :param success: Task was successful or unsuccessful
    :param http_status_code: HTTP status code for indication
    :param reason: reason, why task failed, humanreadable
    :param exception exception, if available
    :return: Dictionary with results
    """
    dict = {
        "success": success,
        "error": str(reason).replace("\n", " ").replace("\r", " ")
        if reason is not None
        else None,
        "http_status": http_status_code,
        "exception": exception,
        "result": result,
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

    sql_string = (
        "INSERT INTO public.api_constraints (action, constraint_type"
        ", constraint_name, constraint_parameter, reference_table, reference_column, c_schema, c_table) "
        "VALUES ('{action}', '{c_type}', '{c_name}', '{c_parameter}', '{r_table}', '{r_column}' , '{c_schema}' "
        ", '{c_table}');".format(
            action=get_or_403(cd, "action"),
            c_type=get_or_403(cd, "constraint_type"),
            c_name=get_or_403(cd, "constraint_name"),
            c_parameter=get_or_403(cd, "constraint_parameter"),
            r_table=get_or_403(cd, "reference_table"),
            r_column=get_or_403(cd, "reference_column"),
            c_schema=schema,
            c_table=table,
        ).replace("'NULL'", "NULL")
    )

    return perform_sql(sql_string)


def queue_column_change(schema, table, column_definition):
    """
    Quere a change to a column
    :param schema: Schema
    :param table: Table
    :param column_definition: Dict with column definition
    :return: Result of database command
    """

    column_definition = api.parser.replace_None_with_NULL(column_definition)

    sql_string = "INSERT INTO public.api_columns (column_name, not_null, data_type, new_name, c_schema, c_table) " "VALUES ('{name}','{not_null}','{data_type}','{new_name}','{c_schema}','{c_table}');".format(
        name=get_or_403(column_definition, "column_name"),
        not_null=get_or_403(column_definition, "not_null"),
        data_type=get_or_403(column_definition, "data_type"),
        new_name=get_or_403(column_definition, "new_name"),
        c_schema=schema,
        c_table=table,
    ).replace(
        "'NULL'", "NULL"
    )

    return perform_sql(sql_string)


def get_column_change(i_id):
    """
    Get one explicit change
    :param i_id: ID of Change
    :return: Change or None, if no change found
    """
    all_changes = get_column_changes()
    for change in all_changes:
        if int(change.get("id")) == int(i_id):
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
        if int(change.get("id")) == int(i_id):
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

    if (
        reviewed is not None
        or changed is not None
        or schema is not None
        or table is not None
    ):
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

    sql = "".join(query)

    response = session.execute(sql)
    session.close()

    return [
        {
            "column_name": column.column_name,
            "not_null": column.not_null,
            "data_type": column.data_type,
            "new_name": column.new_name,
            "reviewed": column.reviewed,
            "changed": column.changed,
            "c_schema": column.c_schema,
            "c_table": column.c_table,
            "id": column.id,
            "exception": column.exception,
        }
        for column in response
    ]


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

    if (
        reviewed is not None
        or changed is not None
        or schema is not None
        or table is not None
    ):
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

    sql = "".join(query)

    response = session.execute(sql)
    session.close()

    return [
        {
            "action": column.action,
            "constraint_type": column.constraint_type,
            "constraint_name": column.constraint_name,
            "constraint_parameter": column.constraint_parameter,
            "reference_table": column.reference_table,
            "reference_column": column.reference_column,
            "reviewed": column.reviewed,
            "changed": column.changed,
            "c_schema": column.c_schema,
            "c_table": column.c_table,
            "id": column.id,
            "exception": column.exception,
        }
        for column in response
    ]


def get_column(d):
    schema = d.get("schema", DEFAULT_SCHEMA)
    table = get_or_403(d, "table")
    name = get_or_403(d, "column")
    return Column("%s.%s" % (table, name), schema=schema)


def get_column_definition_query(d):
    name = get_or_403(d, "name")
    args = []
    kwargs = {}
    dt_string = get_or_403(d, "data_type")
    dt, autoincrement = parse_type(dt_string)

    if autoincrement:
        d["autoincrement"] = True

    for fk in d.get("foreign_key", []):
        fkschema = fk.get("schema", DEFAULT_SCHEMA)
        if fkschema is None:
            fkschema = DEFAULT_SCHEMA

        fktable = Table(get_or_403(fk, "table"), MetaData(), schema=fkschema)

        fkcolumn = Column(get_or_403(fk, "column"))

        fkcolumn.table = fktable

        args.append(ForeignKey(fkcolumn))

    if "autoincrement" in d:
        kwargs["autoincrement"] = d["autoincrement"]

    if not d.get("is_nullable", True):
        kwargs["nullable"] = d["is_nullable"]  # True

    if d.get("primary_key", False):
        kwargs["primary_key"] = True

    if "column_default" in d:
        kwargs["default"] = api.parser.read_pgvalue(d["column_default"])

    if d.get("character_maximum_length", False):
        dt = dt(int(d["character_maximum_length"]))

    c = Column(name, dt, *args, **kwargs)

    return c


def column_alter(query, context, schema, table, column):
    if column == "id":
        raise APIError("You cannot alter the id column")
    alter_preamble = "ALTER TABLE {schema}.{table} ALTER COLUMN {column} ".format(
        schema=schema, table=table, column=column
    )
    if "data_type" in query:
        sql = alter_preamble + "SET DATA TYPE " + read_pgid(query["data_type"])
        if "character_maximum_length" in query:
            sql += (
                "(" + api.parser.read_pgvalue(query["character_maximum_length"]) + ")"
            )
        perform_sql(sql)
    if "is_nullable" in query:
        if read_bool(query["is_nullable"]):
            sql = alter_preamble + " DROP NOT NULL"
        else:
            sql = alter_preamble + " SET NOT NULL"
        perform_sql(sql)
    if "column_default" in query:
        value = api.parser.read_pgvalue(query["column_default"])
        sql = alter_preamble + "SET DEFAULT " + value
        perform_sql(sql)
    if "name" in query:
        sql = (
            "ALTER TABLE {schema}.{table} RENAME COLUMN {column} TO "
            + read_pgid(query["name"])
        ).format(schema=schema, table=table, column=column)
        perform_sql(sql)
    return get_response_dict(success=True)


def column_add(schema, table, column, description):
    description["name"] = column
    settings = get_column_definition_query(description)
    name = settings.name
    s = "ALTER TABLE {schema}.{table} ADD COLUMN {name} {type}".format(
        schema="{schema}", table="{table}", name=name, type=str(settings.type)
    )
    edit_table = get_edit_table_name(schema, table)
    insert_table = get_insert_table_name(schema, table)
    perform_sql(s.format(schema=schema, table=table))
    # Do the same for update and insert tables.
    meta_schema = get_meta_schema_name(schema)
    perform_sql(s.format(schema=meta_schema, table=edit_table))

    meta_schema = get_meta_schema_name(schema)
    perform_sql(s.format(schema=meta_schema, table=insert_table))
    return get_response_dict(success=True)


def table_create(schema, table, columns, constraints_definitions, cursor, table_metadata=None):
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

    # id_columns = [c for c in columns if c['name'] == 'id']
    # if not id_columns:
    #   raise APIError('Your table must have one column "id" of type "bigserial"')
    # cid = id_columns[0]
    # if not get_or_403(cid, 'data_type').lower() == 'bigserial':
    #    raise APIError('Your column "id" must have type "bigserial"')

    if table_metadata is not None:
        omi_dialect = OmiDialect()
        try:
            comment_on_table = omi_dialect._parser().parse(table_metadata)
        except ParserException as e:
            raise APIError(str(e))
        comment_on_table = json.dumps(omi_dialect.compile(comment_on_table))
    else:
        comment_on_table = None

    metadata = MetaData()

    columns = [get_column_definition_query(c) for c in columns]

    constraints = []

    for constraint in constraints_definitions:
        constraint_type = constraint.get("constraint_type") or constraint.get("type")
        if constraint_type is None:
            raise APIError("constraint_type required in %s" % str(constraint))

        constraint_type = constraint_type.lower().replace(" ", "_")
        if constraint_type == "primary_key":
            kwargs = {}
            cname = constraint.get("name")
            if cname:
                kwargs["name"] = cname
            if "columns" in constraint:
                ccolumns = constraint["columns"]
            else:
                ccolumns = [constraint["constraint_parameter"]]
            constraints.append(sa.schema.PrimaryKeyConstraint(*ccolumns, **kwargs))
        elif constraint_type == "unique":
            kwargs = {}
            cname = constraint.get("name")
            if cname:
                kwargs["name"] = cname
            if "columns" in constraint:
                ccolumns = constraint["columns"]
            else:
                ccolumns = [constraint["constraint_parameter"]]
            constraints.append(sa.schema.UniqueConstraint(*ccolumns, **kwargs))

    t = Table(table, metadata, *(columns + constraints), schema=schema, comment=comment_on_table)
    t.create(_get_engine())

    return get_response_dict(success=True)


def table_change_column(column_definition):
    """
    Changes a table column.
    :param schema: schema
    :param table: table
    :param column_definition: column definition according to Issue #184
    :return: Dictionary with results
    """

    schema = get_or_403(column_definition, "c_schema")
    table = get_or_403(column_definition, "c_table")

    # Check if column exists
    existing_column_description = describe_columns(schema, table)

    if len(existing_column_description) <= 0:
        return get_response_dict(False, 400, "table is not defined.")

    # There is a table named schema.table.
    sql = []

    start_name = get_or_403(column_definition, "column_name")
    current_name = get_or_403(column_definition, "column_name")

    if current_name in existing_column_description:
        # Column exists and want to be changed

        # Figure out, which column should be changed and constraint or datatype or name should be changed

        if get_or_403(column_definition, "new_name") is not None:
            # Rename table
            sql.append(
                "ALTER TABLE {schema}.{table} RENAME COLUMN {name} TO {new_name};".format(
                    schema=schema,
                    table=table,
                    name=current_name,
                    new_name=column_definition["new_name"],
                )
            )
            # All other operations should work with new name
            current_name = column_definition["new_name"]

        cdef_datatype = column_definition.get("data_type")
        # TODO: Fix rudimentary handling of datatypes
        if (
            cdef_datatype is not None
            and cdef_datatype
            != existing_column_description[column_definition["name"]]["data_type"]
        ):
            sql.append(
                "ALTER TABLE {schema}.{table} ALTER COLUMN {c_name} TYPE {c_datatype};".format(
                    schema=schema,
                    table=table,
                    c_name=current_name,
                    c_datatype=column_definition["data_type"],
                )
            )

        c_null = "NO" in existing_column_description[start_name]["is_nullable"]
        cdef_null = column_definition.get("not_null")
        if cdef_null is not None and c_null != cdef_null:
            if c_null:
                # Change to nullable
                sql.append(
                    "ALTER TABLE {schema}.{table} ALTER COLUMN {c_name} DROP NOT NULL;".format(
                        schema=schema, table=table, c_name=current_name
                    )
                )
            else:
                # Change to not null
                sql.append(
                    "ALTER TABLE {schema}.{table} ALTER COLUMN {c_name} SET NOT NULL;".format(
                        schema=schema, table=table, c_name=current_name
                    )
                )
    else:
        # Column does not exist and should be created
        # Request will end in 500, if an argument is missing.
        sql.append(
            "ALTER TABLE {schema}.{table} ADD {c_name} {c_datatype} {c_notnull};".format(
                schema=schema,
                table=table,
                c_name=current_name,
                c_datatype=get_or_403(column_definition, "data_type"),
                c_notnull="NOT NULL" if column_definition.get("notnull", False) else "",
            )
        )

    sql_string = "".join(sql)

    return perform_sql(sql_string)


def table_change_constraint(table, constraint_definition):
    """
    Changes constraint of table
    :param schema: schema
    :param table: table
    :param constraint_definition: constraint definition according to Issue #184
    :return: Dictionary with results
    """

    table = get_or_403(constraint_definition, "c_table")
    schema = get_or_403(constraint_definition, "c_schema")

    existing_column_description = describe_columns(schema, table)

    if len(existing_column_description) <= 0:
        raise APIError("Table does not exist")

    # There is a table named schema.table.
    sql = []

    if "ADD" in get_or_403(constraint_definition, "action"):
        ctype = get_or_403(constraint_definition, "constraint_type").lower()
        if ctype == "foreign key":
            columns = [
                get_column(c) for c in get_or_403(constraint_definition, "columns")
            ]

            refcolumns = [
                get_column(c) for c in get_or_403(constraint_definition, "refcolumns")
            ]

            constraint = sa.ForeignKeyConstraint(columns, refcolumns)
            constraint.create(_get_engine())
        elif ctype == "primary key":
            columns = [
                get_column(c) for c in get_or_403(constraint_definition, "columns")
            ]
            constraint = sa.PrimaryKeyConstraint(columns)
            constraint.create(_get_engine())
        elif ctype == "unique":
            columns = [
                get_column(c) for c in get_or_403(constraint_definition, "columns")
            ]
            constraint = sa.UniqueConstraint(*columns)
            constraint.create(_get_engine())
        elif ctype == "check":
            raise APIError("Not supported")
            constraint_class = sa.CheckConstraint
    elif "DROP" in constraint_definition["action"]:
        sql.append(
            "ALTER TABLE {schema}.{table} DROP CONSTRAINT {constraint_name}".format(
                schema=schema,
                table=table,
                constraint_name=constraint_definition["constraint_name"],
            )
        )

    sql_string = "".join(sql)

    return perform_sql(sql_string)


def put_rows(schema, table, column_data):
    keys = list(column_data.keys())
    values = list(column_data.values())

    values = ["'{0}'".format(value) for value in values]

    sql = "INSERT INTO {schema}.{table} ({keys}) VALUES({values})".format(
        schema=schema, table=table, keys=",".join(keys), values=",".join(values)
    )

    return perform_sql(sql)


"""
ACTIONS FROM OLD API
"""


def _get_table(schema, table):
    engine = _get_engine()
    metadata = MetaData(bind=_get_engine())

    return Table(table, metadata, autoload=True, autoload_with=engine, schema=schema)


def __internal_select(query, context):
    engine = _get_engine()
    context2 = dict(user=context.get("user"))
    context2.update(open_raw_connection({}, context2))
    try:
        context2.update(open_cursor({}, context2))
        try:
            rows = data_search(query, context2)
            cursor = load_cursor_from_context(context2)
            rows["data"] = [x for x in cursor.fetchall()]
        finally:
            close_cursor({}, context2)
    finally:
        close_raw_connection({}, context2)
    return rows


def __change_rows(request, context, target_table, setter, fields=None):
    orig_table = read_pgid(request["table"])
    query = {
        "from": {
            "type": "table",
            "schema": read_pgid(request.get("schema", DEFAULT_SCHEMA)),
            "table": orig_table,
        }
    }

    if "where" in request:
        query["where"] = request["where"]

    if fields:
        query["fields"] = [{"type": "column", "column": read_pgid(f)} for f in fields]

    user = context["user"].name

    rows = __internal_select(query, dict(context))

    message = request.get("message", None)
    meta_fields = list(api.parser.set_meta_info("update", user, message).items())
    if fields is None:
        fields = [field[0] for field in rows["description"]]
    fields += [f[0] for f in meta_fields]

    table_name = orig_table
    meta = MetaData(bind=_get_engine())
    table = Table(
        table_name, meta, autoload=True, schema=request.get("schema", DEFAULT_SCHEMA)
    )
    pks = [c for c in table.columns if c.primary_key]

    inserts = []
    cursor = load_cursor_from_context(context)
    if rows["data"]:
        for row in rows["data"]:
            insert = []
            for (key, value) in list(zip(fields, row)) + meta_fields:
                if not api.parser.is_pg_qual(key):
                    raise APIError("%s is not a PostgreSQL identifier" % key)
                if key in setter:
                    if not (key in pks and value != setter[key]):
                        value = setter[key]
                    else:
                        raise InvalidRequest("Primary keys must remain unchanged.")
                insert.append((key, value))

            inserts.append(dict(insert))
        # Add metadata for insertions
        schema = request.get("schema", DEFAULT_SCHEMA)
        meta_schema = (
            get_meta_schema_name(schema) if not schema.startswith("_") else schema
        )

        insert_table = _get_table(meta_schema, target_table)
        query = insert_table.insert(values=inserts)
        _execute_sqla(query, cursor)
    return {"rowcount": rows["rowcount"]}


def data_delete(request, context=None):
    orig_table = get_or_403(request, "table")
    if orig_table.startswith("_") or orig_table.endswith("_cor"):
        raise APIError("Insertions on meta tables is not allowed", status=403)
    orig_schema = request.get("schema", DEFAULT_SCHEMA)

    schema, table = get_table_name(orig_schema, orig_table)

    if schema is None:
        schema = DEFAULT_SCHEMA

    assert_permission(context["user"], table, login_models.DELETE_PERM, schema=schema)

    target_table = get_delete_table_name(orig_schema, orig_table)
    setter = []
    cursor = load_cursor_from_context(context)
    result = __change_rows(request, context, target_table, setter, ["id"])
    if orig_schema in PLAYGROUNDS + UNVERSIONED_SCHEMAS:
        apply_changes(schema, table, cursor)
    return result


def data_update(request, context=None):
    orig_table = read_pgid(get_or_403(request, "table"))
    if orig_table.startswith("_") or orig_table.endswith("_cor"):
        raise APIError("Insertions on meta tables is not allowed", status=403)
    orig_schema = read_pgid(request.get("schema", DEFAULT_SCHEMA))
    schema, table = get_table_name(orig_schema, orig_table)

    if schema is None:
        schema = DEFAULT_SCHEMA

    assert_permission(context["user"], table, login_models.WRITE_PERM, schema=schema)

    target_table = get_edit_table_name(orig_schema, orig_table)
    setter = get_or_403(request, "values")
    if isinstance(setter, list):
        if "fields" not in request:
            raise APIError("values passed in list format without field info")
        field_names = [read_pgid(d["column"]) for d in request["fields"]]
        setter = dict(zip(field_names, setter))
    cursor = load_cursor_from_context(context)
    result = __change_rows(request, context, target_table, setter)
    if orig_schema in PLAYGROUNDS + UNVERSIONED_SCHEMAS:
        apply_changes(schema, table, cursor)
    return result


def data_insert_check(schema, table, values, context):

    engine = _get_engine()
    session = sessionmaker(bind=engine)()
    query = (
        "SELECT array_agg(column_name::text) as columns, conname, "
        "   contype AS type "
        "FROM pg_constraint AS conkeys "
        "JOIN information_schema.constraint_column_usage AS ccu "
        "   ON ccu.constraint_name = conname "
        "WHERE table_name='{table}' "
        "   AND table_schema='{schema}' "
        "   AND conrelid='{schema}.{table}'::regclass::oid "
        "GROUP BY conname, contype;".format(table=table, schema=schema)
    )
    response = session.execute(query)
    session.close()

    for constraint in response:
        columns = constraint.columns
        if constraint.type.lower() == "c":
            pass
        elif constraint.type.lower() == "f":
            pass
        elif constraint.type.lower() in ["u", "p"]:
            # Load data selected by the from_select-clause
            # TODO: I guess this should not be done this way.
            #       Use joins instead to avoid piping your results through
            #       python.
            if isinstance(values, sa.sql.expression.Select):
                values = engine.execute(values)
            for row in values:
                # TODO: This is horribly inefficient!
                query = {
                    "from": {"type": "table", "schema": schema, "table": table},
                    "where": {
                        "type": "operator",
                        "operator": "AND",
                        "operands": [
                            {
                                "operands": [
                                    {"type": "column", "column": c},
                                    {"type": "value", "value": _load_value(row[c])}
                                    if c in row
                                    else {"type": "value"},
                                ],
                                "operator": "=",
                                "type": "operator",
                            }
                            for c in columns
                        ],
                    },
                    "fields": [{"type": "column", "column": f} for f in columns],
                }
                rows = __internal_select(query, context)
                if rows["data"]:
                    raise APIError(
                        "Action violates constraint {cn}. Failing row was {row}".format(
                            cn=constraint.conname,
                            row="("
                            + (
                                ", ".join(
                                    str(row[c]) for c in row if not c.startswith("_")
                                )
                            ),
                        )
                        + ")"
                    )

    for column_name, column in describe_columns(schema, table).items():
        if not column.get("is_nullable", True):
            for row in values:
                val = row.get(column_name, None)
                if val is None or (isinstance(val, str) and val.lower() == "null"):
                    if column_name in row or not column.get("column_default", None):
                        raise APIError(
                            "Action violates not-null constraint on {col}. Failing row was {row}".format(
                                col=column_name,
                                row="("
                                + (
                                    ", ".join(
                                        str(row[c])
                                        for c in row
                                        if not c.startswith("_")
                                    )
                                ),
                            )
                            + ")"
                        )


def _load_value(v):
    if isinstance(v, str):
        if v.isdigit():
            return int(v)
    return v


def data_insert(request, context=None):
    cursor = load_cursor_from_context(context)
    # If the insert request is not for a meta table, change the request to do so
    orig_table = get_or_403(request, "table")
    if orig_table.startswith("_") or orig_table.endswith("_cor"):
        raise APIError("Insertions on meta tables is not allowed", status=403)
    orig_schema = request.get("schema", DEFAULT_SCHEMA)

    schema, table = get_table_name(orig_schema, orig_table)

    if schema is None:
        schema = DEFAULT_SCHEMA

    assert_permission(context["user"], table, login_models.WRITE_PERM, schema=schema)

    mapper = {orig_schema: schema, orig_table: table}

    request["table"] = get_insert_table_name(orig_schema, orig_table)
    if not orig_schema.startswith("_"):
        request["schema"] = "_" + orig_schema

    query, values = api.parser.parse_insert(request, context)
    data_insert_check(orig_schema, orig_table, values, context)
    _execute_sqla(query, cursor)
    description = cursor.description
    response = {}
    if description:
        response["description"] = [
            [
                col.name,
                col.type_code,
                col.display_size,
                col.internal_size,
                col.precision,
                col.scale,
                col.null_ok,
            ]
            for col in description
        ]
    response["rowcount"] = cursor.rowcount
    if schema in PLAYGROUNDS or orig_schema in UNVERSIONED_SCHEMAS:
        apply_changes(schema, table, cursor)

    return response


def _execute_sqla(query, cursor):
    dialect = _get_engine().dialect
    try:
        compiled = query.compile(dialect=dialect)
    except exc.SQLAlchemyError as e:
        raise APIError(repr(e))
    try:
        params = dict(compiled.params)
        for key, value in params.items():
            if isinstance(value, dict):
                if dialect._json_serializer is None:
                    params[key] = json.dumps(value)
                else:
                    params[key] = dialect._json_serializer(value)
        cursor.execute(str(compiled), params)
    except (psycopg2.DataError, exc.IdentifierError, psycopg2.IntegrityError) as e:
        raise APIError(repr(e))
    except psycopg2.InternalError as e:
        if re.match(r"Input geometry has unknown \(\d+\) SRID", repr(e)):
            # Return only SRID errors
            raise APIError(repr(e))
        else:
            raise e
    except psycopg2.ProgrammingError as e:
        if e.pgcode in [
            "42703",  # undefined_column
            "42883",  # undefined_function
            "42P01",  # undefined_table
            "42P02",  # undefined_parameter
            "42704",  # undefined_object
        ]:
            # Return only `function does not exists` errors
            raise APIError(e.diag.message_primary)
        else:
            raise e
    except psycopg2.DatabaseError as e:
        # Other DBAPIErrors should not be reflected to the client.
        raise e
    except:
        raise


def process_value(val):
    if isinstance(val, str):
        return "'" + val.replace("'", "\\'") + "'"
    if isinstance(val, datetime):
        return "'" + str(val) + "'"
    if val is None:
        return "null"
    else:
        return str(val)


def data_search(request, context=None):
    query = api.parser.parse_select(request)
    cursor = load_cursor_from_context(context)
    _execute_sqla(query, cursor)
    description = [
        [
            col.name,
            col.type_code,
            col.display_size,
            col.internal_size,
            col.precision,
            col.scale,
            col.null_ok,
        ]
        for col in cursor.description
    ]
    result = {"description": description, "rowcount": cursor.rowcount}
    return result


def _get_count(q):
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    count = q.session.execute(count_q).scalar()
    return count


def count_all(request, context=None):
    table = get_or_403(request, "table")
    schema = get_or_403(request, "schema")
    engine = _get_engine()
    session = sessionmaker(bind=engine)()
    t = _get_table(schema, table)
    return session.query(t).count()  # _get_count(session.query(t))


def _get_header(results):
    header = []
    for field in results.cursor.description:
        header.append({"id": field[0], "type": field[1]})  # .decode('utf-8'),
    return header


def analyze_columns(schema, table):
    engine = _get_engine()
    result = engine.execute(
        "select column_name as id, data_type as type from information_schema.columns where table_name = '{table}' and table_schema='{schema}';".format(
            schema=schema, table=table
        )
    )
    return [{"id": get_or_403(r, "id"), "type": get_or_403(r, "type")} for r in result]


def clear_dict(d):
    return {
        k.replace(" ", "_"): d[k] if not isinstance(d[k], dict) else clear_dict(d[k])
        for k in d
    }


def create_meta(schema, table):
    meta_schema = get_meta_schema_name(schema)

    if not has_schema({"schema": "_" + schema}):
        create_meta_schema(schema)

    get_edit_table_name(schema, table)
    # Table for inserts
    get_insert_table_name(schema, table)


def get_comment_table(schema, table):
    engine = _get_engine()

    # https://www.postgresql.org/docs/9.5/functions-info.html
    sql_string = "select obj_description('{schema}.{table}'::regclass::oid, 'pg_class');".format(
        schema=schema, table=table
    )
    res = engine.execute(sql_string)
    if res:
        jsn = res.first().obj_description
        if jsn:
            jsn = jsn.replace("\n", "")
        else:
            return {}
        try:
            return json.loads(jsn)
        except ValueError:
            return {"error": "No json format", "description": jsn}
    else:
        return {}


def data_info(request, context=None):
    return request


def connect():
    engine = _get_engine()
    insp = sa.inspect(engine)
    return insp


def has_schema(request, context=None):
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.has_schema(conn, get_or_403(request, "schema"))
    finally:
        conn.close()
    return result


def has_table(request, context=None):
    engine = _get_engine()
    schema = request.pop("schema", DEFAULT_SCHEMA)
    table = get_or_403(request, "table")
    conn = engine.connect()
    try:
        result = engine.dialect.has_table(conn, table, schema=schema)
    finally:
        conn.close()
    return result


def has_sequence(request, context=None):
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.has_sequence(
            conn,
            get_or_403(request, "sequence_name"),
            schema=request.get("schema", DEFAULT_SCHEMA),
        )
    finally:
        conn.close()
    return result


def has_type(request, context=None):
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.has_schema(
            conn,
            get_or_403(request, "sequence_name"),
            schema=request.get("schema", DEFAULT_SCHEMA),
        )
    finally:
        conn.close()
    return result


def get_table_oid(request, context=None):
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.get_table_oid(
            conn,
            get_or_403(request, "table"),
            schema=request.get("schema", DEFAULT_SCHEMA),
            **request
        )
    except sa.exc.NoSuchTableError as e:
        raise ConnectionError(str(e))
    finally:
        conn.close()
    return result


def get_schema_names(request, context=None):
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.get_schema_names(engine.connect(), **request)
    finally:
        conn.close()
    return result


def get_table_names(request, context=None):
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.get_table_names(
            conn, schema=request.pop("schema", DEFAULT_SCHEMA), **request
        )
    finally:
        conn.close()
    return result


def get_view_names(request, context=None):
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.get_view_names(
            conn, schema=request.pop("schema", DEFAULT_SCHEMA), **request
        )
    finally:
        conn.close()
    return result


def get_view_definition(request, context=None):
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.get_schema_names(
            conn,
            get_or_403(request, "view_name"),
            schema=request.pop("schema", DEFAULT_SCHEMA),
            **request
        )
    finally:
        conn.close()
    return result


def get_columns(request, context=None):
    engine = _get_engine()
    connection = engine.connect()

    table_name = get_or_403(request, "table")
    schema = request.pop("schema", DEFAULT_SCHEMA)

    # We need to translate the info_cache from a json-friendly format to the
    # conventional one
    info_cache = None
    if request.get("info_cache"):
        info_cache = {
            ("get_columns", tuple(k.split("+")), tuple()): v
            for k, v in request.get("info_cache", {}).items()
        }

    try:
        table_oid = engine.dialect.get_table_oid(
            connection, table_name, schema, info_cache=info_cache
        )
    except sa.exc.NoSuchTableError as e:
        raise ConnectionError(str(e))
    SQL_COLS = """
                SELECT a.attname,
                  pg_catalog.format_type(a.atttypid, a.atttypmod),
                  (SELECT pg_catalog.pg_get_expr(d.adbin, d.adrelid)
                    FROM pg_catalog.pg_attrdef d
                   WHERE d.adrelid = a.attrelid AND d.adnum = a.attnum
                   AND a.atthasdef)
                  AS DEFAULT,
                  a.attnotnull, a.attnum, a.attrelid as table_oid
                FROM pg_catalog.pg_attribute a
                WHERE a.attrelid = :table_oid
                AND a.attnum > 0 AND NOT a.attisdropped
                ORDER BY a.attnum
            """
    s = sql.text(
        SQL_COLS,
        bindparams=[sql.bindparam("table_oid", type_=sqltypes.Integer)],
        typemap={"attname": sqltypes.Unicode, "default": sqltypes.Unicode},
    )
    c = connection.execute(s, table_oid=table_oid)
    rows = c.fetchall()

    domains = engine.dialect._load_domains(connection)

    enums = dict(
        (
            "%s.%s" % (rec["schema"], rec["name"])
            if not rec["visible"]
            else rec["name"],
            rec,
        )
        for rec in engine.dialect._load_enums(connection, schema="*")
    )

    columns = [
        (name, format_type, default, notnull, attnum, table_oid)
        for name, format_type, default, notnull, attnum, table_oid in rows
    ]

    # format columns
    return {"columns": columns, "domains": domains, "enums": enums}


def get_pk_constraint(request, context=None):
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.get_pk_constraint(
            conn,
            get_or_403(request, "table"),
            schema=request.pop("schema", DEFAULT_SCHEMA),
            **request
        )
    finally:
        conn.close()
    return result


def get_foreign_keys(request, context=None):
    engine = _get_engine()
    conn = engine.connect()
    if not request.get("schema", None):
        request["schema"] = DEFAULT_SCHEMA
    try:
        result = engine.dialect.get_foreign_keys(
            conn,
            get_or_403(request, "table"),
            postgresql_ignore_search_path=request.pop(
                "postgresql_ignore_search_path", False
            ),
            **request
        )
    finally:
        conn.close()
    return result


def get_indexes(request, context=None):
    engine = _get_engine()
    conn = engine.connect()
    if not request.get("schema", None):
        request["schema"] = DEFAULT_SCHEMA
    try:
        result = engine.dialect.get_indexes(
            conn, get_or_403(request, "table"), **request
        )
    finally:
        conn.close()
    return result


def get_unique_constraints(request, context=None):
    engine = _get_engine()
    conn = engine.connect()
    if not request.get("schema", None):
        request["schema"] = DEFAULT_SCHEMA
    try:
        result = engine.dialect.get_foreign_keys(
            conn, get_or_403(request, "table"), **request
        )
    finally:
        conn.close()
    return result


def __get_connection(request):
    # TODO: Implement session-based connection handler
    engine = _get_engine()
    return engine.connect()


def get_isolation_level(request, context):
    engine = _get_engine()
    cursor = load_cursor_from_context(context)
    result = engine.dialect.get_isolation_level(cursor)
    return result


def set_isolation_level(request, context):
    level = request.get("level", None)
    engine = _get_engine()
    cursor = load_cursor_from_context(context)
    try:
        engine.dialect.set_isolation_level(cursor, level)
    except exc.ArgumentError as ae:
        return _response_error(ae.message)
    return __response_success()


def do_begin_twophase(request, context):
    xid = request.get("xid", None)
    engine = _get_engine()
    cursor = load_cursor_from_context(context)
    engine.dialect.do_begin_twophase(cursor, xid)
    return __response_success()


def do_prepare_twophase(request, context):
    xid = request.get("xid", None)
    engine = _get_engine()
    cursor = load_cursor_from_context(context)
    engine.dialect.do_prepare_twophase(cursor, xid)
    return __response_success()


def do_rollback_twophase(request, context):
    xid = request.get("xid", None)
    is_prepared = request.get("is_prepared", True)
    recover = request.get("recover", False)
    engine = _get_engine()
    cursor = load_cursor_from_context(context)
    engine.dialect.do_rollback_twophase(
        cursor, xid, is_prepared=is_prepared, recover=recover
    )
    return __response_success()


def do_commit_twophase(request, context):
    xid = request.get("xid", None)
    is_prepared = request.get("is_prepared", True)
    recover = request.get("recover", False)
    engine = _get_engine()
    cursor = load_cursor_from_context(context)
    engine.dialect.do_commit_twophase(
        cursor, xid, is_prepared=is_prepared, recover=recover
    )
    return __response_success()


def do_recover_twophase(request, context):
    engine = _get_engine()
    cursor = load_cursor_from_context(context)
    return engine.dialect.do_commit_twophase(cursor)


def _get_default_schema_name(self, connection):
    return connection.scalar("select current_schema()")


def open_raw_connection(request, context):
    session_context = SessionContext(owner=context.get("user"))
    return {"connection_id": session_context.connection._id}


def commit_raw_connection(request, context):
    connection = load_session_from_context(context).connection
    connection.commit()
    return __response_success()


def rollback_raw_connection(request, context):
    load_session_from_context(context).rollback()
    return __response_success()


def close_raw_connection(request, context):
    load_session_from_context(context).close()
    return __response_success()


def close_all_connections(request, context):
    close_all_for_user(request, context)
    return __response_success()


def open_cursor(request, context, named=False):
    session_context = load_session_from_context(context)
    cursor_id = session_context.open_cursor(named=named)
    return {"cursor_id": cursor_id}


def close_cursor(request, context):
    session_context = load_session_from_context(context)
    cursor_id = int(context["cursor_id"])
    session_context.close_cursor(cursor_id)
    return {"cursor_id": cursor_id}


def fetchone(request, context):
    cursor = load_cursor_from_context(context)
    row = cursor.fetchone()
    if row:
        row = [_translate_fetched_cell(cell) for cell in row]
        return row
    else:
        return row


def fetchall(context):
    cursor = load_cursor_from_context(context)
    return cursor.fetchall()


def fetchmany(request, context):
    cursor = load_cursor_from_context(context)
    return cursor.fetchmany(request["size"])


def get_comment_table_name(schema, table, create=True):
    table_name = "_" + table + "_cor"
    if create and not has_table(
        {"schema": get_meta_schema_name(schema), "table": table_name}
    ):
        create_edit_table(schema, table)
    return table_name


def get_delete_table_name(schema, table, create=True):
    table_name = '_' + table + '_delete'
    if create:
        create_delete_table(schema, table)
    return table_name


def get_edit_table_name(schema, table, create=True):
    table_name = '_' + table + '_edit'
    if create:
        create_edit_table(schema, table)
    return table_name


def get_insert_table_name(schema, table, create=True):
    table_name = '_' + table + '_insert'
    if create:
        create_insert_table(schema, table)
    return table_name


def get_meta_schema_name(schema):
    return "_" + schema


def create_meta_schema(schema):
    """Create a schema to store schema meta information

    :param schema: Name of the schema
    :return: None
    """
    engine = _get_engine()
    query = "CREATE SCHEMA {schema}".format(schema=get_meta_schema_name(schema))
    connection = engine.connect()
    connection.execute(query)


def create_meta_table(schema, table, meta_table, meta_schema=None, include_indexes=True):
    if not meta_schema:
        meta_schema = get_meta_schema_name(schema)
    if not has_table(dict(schema=meta_schema, table=meta_table)):
        query = 'CREATE TABLE "{meta_schema}"."{edit_table}" ' \
                '(LIKE "{schema}"."{table}"'
        if include_indexes:
            query += 'INCLUDING ALL EXCLUDING INDEXES, PRIMARY KEY (_id) '
        query += ') INHERITS (_edit_base);'
        query = query.format(
            meta_schema=meta_schema,
            edit_table=meta_table,
            schema=schema,
            table=table)
        engine = _get_engine()
        engine.execute(query)


def create_delete_table(schema, table, meta_schema=None):
    meta_table = get_delete_table_name(schema, table, create=False)
    create_meta_table(schema, table, meta_table, meta_schema, include_indexes=False)


def create_edit_table(schema, table, meta_schema=None):
    meta_table = get_edit_table_name(schema, table, create=False)
    create_meta_table(schema, table, meta_table, meta_schema)



def create_insert_table(schema, table, meta_schema=None):
    meta_table = get_insert_table_name(schema, table, create=False)
    create_meta_table(schema, table, meta_table, meta_schema)


def create_comment_table(schema, table, meta_schema=None):
    if not meta_schema:
        meta_schema = get_meta_schema_name(schema)
    engine = _get_engine()
    query = (
        "CREATE TABLE {schema}.{table} (PRIMARY KEY (_id)) "
        "INHERITS (_comment_base); ".format(
            schema=meta_schema, table=get_comment_table_name(table)
        )
    )
    engine.execute(query)


def getValue(schema, table, column, id):
    sql = "SELECT {column} FROM {schema}.{table} WHERE id={id}".format(
        column=column, schema=schema, table=table, id=id
    )

    engine = _get_engine()
    session = sessionmaker(bind=engine)()

    try:
        result = session.execute(sql)

        returnValue = None
        for row in result:
            returnValue = row[column]

        return returnValue
    except Exception as e:
        print("SQL Action failed. \n Error:\n" + str(e))
        session.rollback()
    finally:
        session.close()
    return None


def apply_changes(schema, table, cursor=None):
    def add_type(d, type):
        d["_type"] = type
        return d

    engine = _get_engine()

    artificial_connection = False

    if cursor is None:
        artificial_connection = True
        connection = engine.raw_connection()
        cursor = connection.cursor()

    try:
        meta_schema = get_meta_schema_name(schema)

        columns = list(describe_columns(schema, table).keys())
        extended_columns = columns + ["_submitted", "_id"]

        insert_table = get_insert_table_name(schema, table)
        cursor.execute(
            "select * "
            "from {schema}.{table} "
            "where _applied = FALSE;".format(schema=meta_schema, table=insert_table)
        )
        changes = [
            add_type(
                {
                    c.name: v
                    for c, v in zip(cursor.description, row)
                    if c.name in extended_columns
                },
                "insert",
            )
            for row in cursor.fetchall()
        ]

        update_table = get_edit_table_name(schema, table)
        cursor.execute(
            "select * "
            "from {schema}.{table} "
            "where _applied = FALSE;".format(schema=meta_schema, table=update_table)
        )
        changes += [
            add_type(
                {
                    c.name: v
                    for c, v in zip(cursor.description, row)
                    if c.name in extended_columns
                },
                "update",
            )
            for row in cursor.fetchall()
        ]

        delete_table = get_delete_table_name(schema, table)
        cursor.execute(
            "select * "
            "from {schema}.{table} "
            "where _applied = FALSE;".format(schema=meta_schema, table=delete_table)
        )
        changes += [
            add_type(
                {
                    c.name: v
                    for c, v in zip(cursor.description, row)
                    if c.name in ["_id", "id", "_submitted"]
                },
                "delete",
            )
            for row in cursor.fetchall()
        ]

        changes = list(changes)
        table_obj = Table(table, MetaData(bind=engine), autoload=True, schema=schema)

        # ToDo: This may require some kind of dependency tree resolution
        for change in sorted(changes, key=lambda x: x["_submitted"]):
            distilled_change = {k: v for k, v in change.items() if k in columns}
            if change["_type"] == "insert":
                apply_insert(cursor, table_obj, distilled_change, change["_id"])
            elif change["_type"] == "update":
                apply_update(cursor, table_obj, distilled_change, change["_id"])
            elif change["_type"] == "delete":
                apply_deletion(cursor, table_obj, distilled_change, change["_id"])

        if artificial_connection:
            connection.commit()
    except:
        if artificial_connection:
            connection.rollback()
        raise
    finally:
        if artificial_connection:
            cursor.close()
            connection.close()


def set_applied(session, table, rid, mode):
    if mode == __INSERT:
        name_map = get_insert_table_name
    elif mode == __DELETE:
        name_map = get_delete_table_name
    elif mode == __UPDATE:
        name_map = get_edit_table_name
    else:
        raise NotImplementedError
    meta_table = Table(
        name_map(table.schema, table.name),
        MetaData(bind=_get_engine()),
        autoload=True,
        schema=get_meta_schema_name(table.schema),
    )
    update_query = (
        meta_table.update()
        .where(meta_table.c._id == rid)
        .values(_applied=True)
        .compile()
    )
    session.execute(str(update_query), update_query.params)


def apply_insert(session, table, row, rid):
    logger.info("apply insert " + str(row))
    query = table.insert().values(row)
    _execute_sqla(query, session)
    set_applied(session, table, rid, __INSERT)


def apply_update(session, table, row, rid):
    logger.info("apply update " + str(row))
    pks = [c.name for c in table.columns if c.primary_key]
    query = table.update(*[getattr(table.c, pk) == row[pk] for pk in pks]).values(row)
    _execute_sqla(query, session)
    set_applied(session, table, rid, __UPDATE)


def apply_deletion(session, table, row, rid):
    logger.info("apply deletion " + str(row))
    query = table.delete().where(*[getattr(table.c, col) == row[col] for col in row])
    _execute_sqla(query, session)
    set_applied(session, table, rid, __DELETE)


def update_meta_search(session, table, schema, insert_only=False):
    exists = False
    if not schema:
        schema = "public"
    if not insert_only:
        # If it is not known whether the table is already registered,
        # we have to check whether it is.
        exists = session.bind().has_table(table, schema=schema)
    if not exists:
        meta = MetaData(bind=session.bind)
        t = sa.Table(table, meta, schema=schema, autoload=True)
        comment = t.comment
        session.execute(
            sa.insert(
                MetaSearch,
                values=[
                    dict(
                        table=table,
                        schema=schema,
                        comment=sa.cast(
                            " ".join((schema, table, comment if comment else "")),
                            TSVECTOR,
                        ),
                    )
                ],
            )
        )
