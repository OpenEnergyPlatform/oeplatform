"""Api actions.

SPDX-FileCopyrightText: 2025 Pierre Francois <https://github.com/Bachibouzouk> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Eike Broda <https://github.com/ebroda>
SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>  © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Tom Heimbrodt <https://github.com/tom-heimbrodt>
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Christian Hofmann <https://github.com/christian-rli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 chrwm <https://github.com/chrwm> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 henhuy <https://github.com/henhuy> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 user <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json
import logging
import re
from copy import deepcopy
from datetime import datetime, timedelta
from typing import cast

import geoalchemy2  # noqa: Although this import seems unused is has to be here
import psycopg2
from django.core.exceptions import PermissionDenied
from django.db.models import Func, Value
from django.http import Http404, HttpRequest
from omi.base import get_metadata_version
from omi.conversion import convert_metadata
from omi.validation import ValidationError, parse_metadata, validate_metadata
from rest_framework.request import Request
from shapely import wkb
from sqlalchemy import Column, ForeignKeyConstraint, MetaData, PrimaryKeyConstraint
from sqlalchemy import Table as SATable
from sqlalchemy import UniqueConstraint, exc, inspect, select, sql, text
from sqlalchemy import types as sqltypes
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.schema import Sequence
from sqlalchemy.sql.expression import Select

import dataedit.metadata
from api.error import APIError
from api.parser import (
    get_column_definition_query,
    get_or_403,
    is_pg_qual,
    parse_insert,
    parse_select,
    read_bool,
    read_pgid,
    read_pgvalue,
    replace_None_with_NULL,
    set_meta_info,
)
from api.sessions import (
    SessionContext,
    close_all_for_user,
    load_cursor_from_context,
    load_session_from_context,
)
from api.utils import check_if_oem_license_exists, validate_schema
from dataedit.models import Embargo, PeerReview, Table
from login.models import myuser as User
from login.permissions import DELETE_PERM, WRITE_PERM
from oedb.connection import (
    AbstractCursor,
    Connection,
    DBAPIConnection,
    Engine,
    ResultProxy,
    Session,
    _get_engine,
)
from oedb.utils import ID_COLUMN_NAME
from oeplatform.settings import SCHEMA_DATA, SCHEMA_DEFAULT_TEST_SANDBOX

logger = logging.getLogger("oeplatform")
pgsql_qualifier = re.compile(r"^[\w\d_\.]+$")


Base = declarative_base()

__INSERT = 0
__UPDATE = 1
__DELETE = 2


def _create_oedb_session():
    """Return a sqlalchemy session to the oedb

    Should only be created once per user request.
    """
    return sessionmaker(bind=_get_engine())()


def delete_sequence(sequence: str, schema: str) -> None:
    seq = Sequence(sequence, schema=schema)
    seq.drop(bind=_get_engine())


def create_sequence(sequence: str, schema: str) -> None:
    seq = Sequence(sequence, schema=schema)
    # FIXME: no permission control
    seq.create(bind=_get_engine())


def get_columns_select(columns: list[str]) -> Select:
    return select(columns=columns)


def get_column_obj(sa_table: SATable, column: str):
    """

    :param talbe: A sqla-table object
    :param column: A column name
    :return: Basically `getattr(table.c, column)` but throws an exception of the
        column does not exists
    """
    tc = sa_table.c
    try:
        return getattr(tc, column)
    except AttributeError:
        raise APIError("Column '%s' does not exist." % column)


def get_table_name(
    schema: str | None, table: str, restrict_schemas: bool = True
) -> tuple[str, str]:
    schema = validate_schema(schema)

    if not has_schema(dict(schema=schema)):
        raise Http404
    if not has_table(dict(schema=schema, table=table)):
        raise Http404
    if schema.startswith("_") or schema == "public" or schema is None:
        raise PermissionDenied

    return schema, table


def table_or_404(table: str) -> Table:
    table_obj = Table.objects.filter(name=table).first()
    if table_obj is None:
        raise APIError("Table doesnot exist", 401)
    return table_obj


def table_or_404_from_dict(dct: dict) -> Table:
    return table_or_404(get_or_403(dct, "table"))


def table_or_404_from_req(request: Request | HttpRequest) -> Table:
    return table_or_404_from_req(request.GET)  # type:ignore TODO


def assert_permission(user, table: str, permission: int) -> None:
    if user.is_anonymous or not isinstance(user, User):
        raise APIError("User is anonymous", 401)

    if user.get_table_permission_level(Table.load(name=table)) < permission:
        raise APIError("Permission denied", 403)


def assert_add_tag_permission(user, table: str, permission: int, schema) -> None:
    """
    Tags can be added to tables that are in any schema. However,
    it is necessary to check whether the user has write permission
    to the table, since not every user should be able to add tags
    to every table.

    Args:
        user (_type_): _description_
        table (_type_): _description_
        permission (_type_): _description_
        schema (_type_): _description_

    Raises:
        PermissionDenied: _description_

    """
    if user.is_anonymous:
        raise APIError("User is anonymous", 401)

    if user.get_table_permission_level(Table.load(name=table)) < permission:
        raise PermissionDenied


def assert_has_metadata(table: str, schema: str) -> bool:
    table_obj = Table.load(name=table)
    if table_obj.oemetadata is None:
        result = False
    else:
        result = True

    return result


def _translate_fetched_cell(cell):
    if isinstance(cell, geoalchemy2.WKBElement):
        return engine_execute(_get_engine(), cell.ST_AsText()).scalar()
    elif isinstance(cell, memoryview):
        return wkb.dumps(wkb.loads(cell.tobytes()), hex=True)
    else:
        return cell


def __response_success():
    return {"success": True}


def _response_error(message: str):
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


def try_parse_metadata(inp) -> tuple[dict | None, str | None]:
    """

    Args:
        inp: string or dict or OEPMetadata

    Returns:
        Tuple[OEPMetadata or None, string or None]:
        The first component is the result of the parsing procedure or `None` if
        the parsing failed. The second component is None, if the parsing failed,
        otherwise an error message.

    Examples:

        >>> from api.actions import try_parse_metadata
        >>> result, error = try_parse_metadata('{"id":"id"}')
        >>> error is None
        True

    """

    if isinstance(inp, dict):
        # already parsed but need to check if metaMetadata version exists

        result = check_if_oem_license_exists(inp)
        if result[1] is not None:
            return result

        # cleanup curser metadata

        return inp, None
    # TODO: is this even needed anymore?
    elif not isinstance(inp, (str, bytes)):
        # in order to use the omi parsers, input needs to be str (or bytes)
        try:
            inp = json.dumps(inp)
        except Exception:
            return None, "Could not serialize json"

    last_err = None

    try:
        parsed_meta = parse_metadata(inp)

        result = check_if_oem_license_exists(parsed_meta)
        if result[1] is not None:
            return result

        return parsed_meta, None
    except ValidationError as e:
        return None, str(e)
    except Exception as e:
        last_err = e
    raise APIError(f"Metadata could not be parsed: {last_err}")


def try_validate_metadata(inp: dict) -> tuple[dict | None, str | None]:
    """

    Args:
        inp: OEPMetadata

    Returns:
        Tuple[str or None, str or None]:
        The first part is the result of the validate procedure or `None` if
        the validation failed. The second part includes the exception message.
    """
    meta = deepcopy(inp)
    last_err = None

    try:
        meta.pop("connection_id", None)
        meta.pop("cursor_id", None)
        meta_str = json.dumps(meta)
        validate_metadata(meta_str, check_license=False)
        return inp, None
    except ValidationError as e:
        return None, str(e)
    except Exception as e:
        last_err = e

    raise APIError(f"Metadata validation failed: {last_err}")


def try_convert_metadata_to_v2(metadata: dict) -> dict:
    valid_oemetadata_versions = ["OEP-1.5.2", "OEP-1.6.0", "OEMetadata-2.0"]
    valid_conversable_oemetadata_versions = ["OEP-1.5.2", "OEP-1.6.0"]
    version = get_metadata_version(metadata)
    if version in valid_conversable_oemetadata_versions:
        converted = convert_metadata(metadata, "OEMetadata-2.0")
        return converted
    # Try to force conversion to v2
    elif version not in valid_oemetadata_versions:
        metadata["metaMetadata"]["metadataVersion"] = "OEP-1.6.0"
        converted = convert_metadata(metadata, "OEMetadata-2.0")
        return converted

    return metadata


def describe_columns(schema, table):
    """
    Loads the description of all columns of the specified table and return their
    description as a dictionary. Each column is identified by its name and
    points to a dictionary containing the information specified
    in https://www.postgresql.org/docs/9.3/static/infoschema-columns.html:

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
        "c.maximum_cardinality, c.dtd_identifier, c.udt_name, c.is_updatable, e.data_type as element_type "  # noqa
        "from INFORMATION_SCHEMA.COLUMNS  c "
        "LEFT JOIN information_schema.element_types e "
        "ON ((c.table_catalog, c.table_schema, c.table_name, 'TABLE', c.dtd_identifier) "  # noqa
        "= (e.object_catalog, e.object_schema, e.object_name, e.object_type, e.collection_type_identifier)) where table_name = "  # noqa
        "'{table}' and table_schema='{schema}';".format(table=table, schema=schema)
    )
    response = session_execute(session, query)

    # Note: cast is only for type checking,
    # should disappear once we migrate to sqlalchemy >= 1.4
    response = cast(ResultProxy, response)

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
    response = session_execute(session, query)
    session.close()

    # Use a single-value dictionary to allow future extension with downward
    # compatibility
    return {column.indexname: {"indexdef": column.indexdef} for column in response}


def describe_constraints(schema, table):
    """
    Loads the description of all constraints of the specified table and return their
    description as a dictionary. Each constraints is identified by its name and
    points to a dictionary containing the following information specified
    in https://www.postgresql.org/docs/9.3/static/infoschema-table-constraints.html:

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
    query = "select constraint_name, constraint_type, is_deferrable, initially_deferred, pg_get_constraintdef(c.oid) as definition from information_schema.table_constraints JOIN pg_constraint AS c  ON c.conname=constraint_name where table_name='{table}' AND constraint_schema='{schema}';".format(  # noqa
        table=table, schema=schema
    )
    response = session_execute(session, query)
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


def perform_sql(sql_statement, parameter: dict | None = None) -> dict:
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
        result = session_execute_parameter(session, sql_statement, parameter)
    except Exception as e:
        logger.error("SQL Action failed. \n Error:\n" + str(e))
        session.rollback()
        raise APIError(str(e))
    else:
        # Why is commit() not part of close() ?
        # I have to commit the changes before closing session.
        # Otherwise the changes are not persistent.
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
        sql = (
            "UPDATE api_columns SET reviewed=True, changed=True WHERE id='{id}'".format(
                id=id
            )
        )
    else:
        ex_str = str(res.get("exception"))
        sql = "UPDATE api_columns SET reviewed=False, changed=False, exception={ex_str} WHERE id='{id}'".format(  # noqa
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
        sql = "UPDATE api_constraints SET reviewed=True, changed=True WHERE id='{id}'".format(  # noqa
            id=id
        )
    else:
        ex_str = str(res.get("exception"))
        sql = "UPDATE api_constraints SET reviewed=False, changed=False, exception={ex_str} WHERE id='{id}'".format(  # noqa
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
    success: bool,
    http_status_code: int = 200,
    reason: str | None = None,
    exception=None,
    result=None,
) -> dict:
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
        "error": (
            str(reason).replace("\n", " ").replace("\r", " ")
            if reason is not None
            else None
        ),
        "http_status": http_status_code,
        "exception": exception,
        "result": result,
    }
    return dict


def queue_constraint_change(schema: str, table: str, constraint_def: dict):
    """
    Queue a change to a constraint
    :param schema: Schema
    :param table: Table
    :param constraint_def: Dict with constraint definition
    :return: Result of database command
    """

    cd = replace_None_with_NULL(constraint_def)

    sql_string = (
        "INSERT INTO public.api_constraints (action, constraint_type"
        ", constraint_name, constraint_parameter, reference_table, reference_column, c_schema, c_table) "  # noqa
        "VALUES ('{action}', '{c_type}', '{c_name}', '{c_parameter}', '{r_table}', '{r_column}' , '{c_schema}' "  # noqa
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


def queue_column_change(schema: str, table: str, column_definition: dict) -> dict:
    """
    Quere a change to a column
    :param schema: Schema
    :param table: Table
    :param column_definition: Dict with column definition
    :return: Result of database command
    """

    column_definition = replace_None_with_NULL(column_definition)

    sql_string = "INSERT INTO public.api_columns (column_name, not_null, data_type, new_name, c_schema, c_table) " "VALUES ('{name}','{not_null}','{data_type}','{new_name}','{c_schema}','{c_table}');".format(  # noqa
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
        if int(change["id"]) == int(i_id):
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
        if int(change["id"]) == int(i_id):
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

    response = session_execute(session, sql)
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

    response = session_execute(session, sql)
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
    schema = d.get("schema", SCHEMA_DEFAULT_TEST_SANDBOX)
    schema = validate_schema(schema)
    table = get_or_403(d, "table")
    name = get_or_403(d, "column")
    return Column("%s.%s" % (table, name), schema=schema)


def column_alter(query, context, schema, table: str, column):
    schema = validate_schema(schema)

    if column == "id":
        raise APIError("You cannot alter the id column")
    alter_preamble = 'ALTER TABLE "{schema}"."{table}" ALTER COLUMN "{column}" '.format(
        schema=schema, table=table, column=column
    )
    if "data_type" in query:
        sql = alter_preamble + "SET DATA TYPE " + read_pgid(query["data_type"])
        if "character_maximum_length" in query:
            sql += "(" + read_pgvalue(query["character_maximum_length"]) + ")"
        perform_sql(sql)
    if "is_nullable" in query:
        if read_bool(query["is_nullable"]):
            sql = alter_preamble + " DROP NOT NULL"
        else:
            sql = alter_preamble + " SET NOT NULL"
        perform_sql(sql)
    if "column_default" in query:
        value = read_pgvalue(query["column_default"])
        sql = alter_preamble + "SET DEFAULT " + value
        perform_sql(sql)
    if "name" in query:
        sql = (
            'ALTER TABLE "{schema}"."{table}" RENAME COLUMN "{column}" TO '
            + read_pgid(query["name"])
        ).format(schema=schema, table=table, column=column)
        perform_sql(sql)
    return get_response_dict(success=True)


def column_add(schema, table: str, column, description):
    schema = validate_schema(schema)
    description["name"] = column
    settings = get_column_definition_query(description)
    name = settings.name
    # NOTE: we format schema/table with placeholders and format again later
    s = 'ALTER TABLE "{schema}"."{table}" ADD COLUMN "{name}" {type}'.format(
        schema="{schema}", table="{table}", name=name, type=str(settings.type)
    )

    # TODO:permission check is still done outside of this function,
    # so we pass user=None
    oedb_table = Table.objects.get(name=table).get_oeb_table_proxy(user=None)

    edit_sa_table = oedb_table._edit_table.get_sa_table()
    insert_sa_table = oedb_table._insert_table.get_sa_table()

    perform_sql(s.format(schema=schema, table=table))
    # Do the same for update and insert tables.
    perform_sql(s.format(schema=edit_sa_table.schema, table=edit_sa_table.name))
    perform_sql(s.format(schema=insert_sa_table.schema, table=insert_sa_table.name))

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
    schema = validate_schema(schema)
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

        # Figure out, which column should be changed and constraint
        # or datatype or name should be changed

        if get_or_403(column_definition, "new_name") is not None:
            # Rename table
            sql.append(
                'ALTER TABLE "{schema}"."{table}" RENAME COLUMN "{name}" TO "{new_name}";'.format(  # noqa
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
                'ALTER TABLE "{schema}"."{table}" ALTER COLUMN "{c_name}" TYPE {c_datatype};'.format(  # noqa
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
                    '"ALTER TABLE "{schema}"."{table}" ALTER COLUMN "{c_name}" DROP NOT NULL;'.format(  # noqa
                        schema=schema, table=table, c_name=current_name
                    )
                )
            else:
                # Change to not null
                sql.append(
                    'ALTER TABLE "{schema}"."{table}" ALTER COLUMN "{c_name}" SET NOT NULL;'.format(  # noqa
                        schema=schema, table=table, c_name=current_name
                    )
                )
    else:
        # Column does not exist and should be created
        # Request will end in 500, if an argument is missing.
        sql.append(
            'ALTER TABLE "{schema}"."{table}" ADD "{c_name}" {c_datatype} {c_notnull};'.format(  # noqa
                schema=schema,
                table=table,
                c_name=current_name,
                c_datatype=get_or_403(column_definition, "data_type"),
                c_notnull="NOT NULL" if column_definition.get("notnull", False) else "",
            )
        )

    sql_string = "".join(sql)

    return perform_sql(sql_string)


def table_change_constraint(constraint_definition):
    """
    Changes constraint of table
    :param schema: schema
    :param table: table
    :param constraint_definition: constraint definition according to Issue #184
    :return: Dictionary with results
    """

    table = get_or_403(constraint_definition, "c_table")
    schema = get_or_403(constraint_definition, "c_schema")
    schema = validate_schema(schema)

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

            constraint = ForeignKeyConstraint(columns, refcolumns)
            constraint.create(_get_engine())
        elif ctype == "primary key":
            columns = [
                get_column(c) for c in get_or_403(constraint_definition, "columns")
            ]
            constraint = PrimaryKeyConstraint(columns)
            constraint.create(_get_engine())
        elif ctype == "unique":
            columns = [
                get_column(c) for c in get_or_403(constraint_definition, "columns")
            ]
            constraint = UniqueConstraint(*columns)
            constraint.create(_get_engine())
        elif ctype == "check":
            raise APIError("Not supported")
    elif "DROP" in constraint_definition["action"]:
        sql.append(
            'ALTER TABLE "{schema}"."{table}" DROP CONSTRAINT "{constraint_name}"'.format(  # noqa
                schema=schema,
                table=table,
                constraint_name=constraint_definition["constraint_name"],
            )
        )

    sql_string = "".join(sql)

    return perform_sql(sql_string)


def put_rows(schema, table: str, column_data):
    keys = list(column_data.keys())
    values = list(column_data.values())

    keys = ['"{0}"'.format(key) for key in keys]
    values = ["'{0}'".format(value) for value in values]

    sql = 'INSERT INTO "{schema}"."{table}" ({keys}) VALUES({values})'.format(
        schema=schema, table=table, keys=",".join(keys), values=",".join(values)
    )

    return perform_sql(sql)


"""
ACTIONS FROM OLD API
"""


def _get_table(schema, table) -> SATable:
    engine = _get_engine()
    metadata = MetaData(bind=_get_engine())

    return SATable(table, metadata, autoload=True, autoload_with=engine, schema=schema)


def get_table_metadata(schema: str, table: str) -> dict:
    django_obj = Table.load(name=table)
    oemetadata = django_obj.oemetadata
    return oemetadata if oemetadata else {}


def __internal_select(query, context):
    # engine = _get_engine()
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


def __change_rows(
    request, context, target_sa_table: SATable, setter, fields=None
) -> dict:
    orig_table = read_pgid(request["table"])
    query: dict = {
        "from": {
            "type": "table",
            "schema": read_pgid(request.get("schema", SCHEMA_DEFAULT_TEST_SANDBOX)),
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
    meta_fields = list(set_meta_info("update", user, message).items())
    if fields is None:
        fields = [field[0] for field in rows["description"]]
    fields += [f[0] for f in meta_fields]

    table_name = orig_table
    meta = MetaData(bind=_get_engine())
    sa_table = SATable(
        table_name,
        meta,
        autoload=True,
        schema=request.get("schema", SCHEMA_DEFAULT_TEST_SANDBOX),
    )

    pks = [c for c in sa_table.columns if c.primary_key]  # type:ignore

    inserts = []
    cursor = load_cursor_from_context(context)
    if rows["data"]:
        for row in rows["data"]:
            insert = []
            for key, value in list(zip(fields, row)) + meta_fields:
                if not is_pg_qual(key):
                    raise APIError("%s is not a PostgreSQL identifier" % key)
                if key in setter:
                    if not (key in pks and value != setter[key]):
                        value = setter[key]
                    else:
                        raise InvalidRequest("Primary keys must remain unchanged.")
                insert.append((key, value))

            inserts.append(dict(insert))
        # Add metadata for insertions
        query = target_sa_table.insert(values=inserts)
        _execute_sqla(query, cursor)
    return {"rowcount": rows["rowcount"]}


def drop_not_null_constraints_from_delete_meta_table(
    meta_table_delete: str, meta_schema: str
) -> None:
    # https://github.com/OpenEnergyPlatform/oeplatform/issues/1548
    # we only want id column (and meta colums, wich start with a "_")

    meta_schema = validate_schema(meta_schema)

    engine = _get_engine()

    # find not nullable columns in meta tables
    query = f"""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = '{meta_table_delete}'
    AND table_schema = '{meta_schema}'
    AND is_nullable = 'NO'
    """
    resp = engine_execute(engine, query).fetchall()
    column_names = [x[0] for x in resp] if resp else []
    # filter meta columns and id
    column_names = [
        c for c in column_names if c != ID_COLUMN_NAME and not c.startswith("_")
    ]

    if not column_names:
        # nothing to do
        return

    # drop not null from these columns
    col_drop = ", ".join(f'ALTER "{c}" DROP NOT NULL' for c in column_names)
    query = f'ALTER TABLE "{meta_schema}"."{meta_table_delete}" {col_drop};'
    engine_execute(engine, query)


def data_insert_check(schema, table: str, values, context):
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
    response = session_execute(session, query)
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
            if isinstance(values, Select):
                values = engine_execute(engine, values)
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
                                    (
                                        {"type": "value", "value": row[c]}
                                        if c in row
                                        else {"type": "value"}
                                    ),
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
                        # TODO: this error message is not clear to users. It is for
                        # example shown if the user attempts to upload a csv data
                        # and some id values from the csv are already available
                        # in the table.
                        raise APIError(
                            "Action violates not-null constraint on {col}. "
                            "Failing row was {row}. Please check if there are "
                            "id values in your upload data that are already "
                            "exist in the table. Primary key's cant be duplicated".format(  # noqa
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


def _execute_sqla(query, cursor: AbstractCursor | Session) -> None:
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
        cursor_execute_parameter(cursor, str(compiled), params)
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
            "42804",  # datatype mismatch
        ]:
            # Return only `function does not exists` errors
            raise APIError(e.diag.message_primary)
        else:
            raise e
    except psycopg2.DatabaseError as e:
        # Other DBAPIErrors should not be reflected to the client.
        raise e
    except Exception:
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


def count_all(request, context=None):
    table = get_or_403(request, "table")
    schema = get_or_403(request, "schema")
    engine = _get_engine()
    session = sessionmaker(bind=engine)()
    sa_table = _get_table(schema, table)
    return session.query(sa_table).count()


def analyze_columns(schema, table):
    engine = _get_engine()
    result = engine_execute(
        engine,
        "select column_name as id, data_type as type from information_schema.columns where table_name = '{table}' and table_schema='{schema}';".format(  # noqa
            schema=schema, table=table
        ),
    )
    return [{"id": get_or_403(r, "id"), "type": get_or_403(r, "type")} for r in result]


def clear_dict(d):
    return {
        k.replace(" ", "_"): d[k] if not isinstance(d[k], dict) else clear_dict(d[k])
        for k in d
    }


def move(from_schema, table: str, to_schema):
    """
    Implementation note:
        Currently we implemented two versions of the move functionality
        this will later be harmonized. See 'move_publish'.
    """
    move_publish(
        from_schema=from_schema,
        table=table,
        to_schema=to_schema,
        embargo_period="none",
    )


def move_publish(from_schema, table: str, to_schema, embargo_period):
    """
    The issue about publishing datatables  in the context of the OEP
    is that tables must be moved physically in the postgreSQL database.
    We need to  move the table in the OEDB to update the data & we need
    to update the table registry in the OEP django database to keep the
    display information up to date.
    This function tackales this issue. It implements a procedure in witch
    the order of execturion matter as for example before updating the
    schema / datatopic it shall be published in we need to check if the
    table is already in that schema & if the table holds and open data
    license in its metadata.


    Implementation note:
        Currently we implemented two versions of the move functionality
        this will later be harmonized. See 'move'.

    Args:

    Returns:

    """

    table_obj = Table.objects.get(name=table)
    validate_open_data_license = table_obj.validate_open_data_license()

    license_check = validate_open_data_license["status"]
    license_error = validate_open_data_license["error"]

    if not license_check:
        raise APIError(
            "A issue with the license from the metadata was found: " f"{license_error}"
        )

    if embargo_period in ["6_months", "1_year"]:
        duration_in_weeks = 26 if embargo_period == "6_months" else 52
        embargo, created = Embargo.objects.get_or_create(
            table=table_obj,
            defaults={
                "duration": embargo_period,
                "date_ended": datetime.now() + timedelta(weeks=duration_in_weeks),
            },
        )
        if not created:
            if embargo.date_started:
                embargo.duration = embargo_period
                embargo.date_ended = embargo.date_started + timedelta(
                    weeks=duration_in_weeks
                )
            else:
                embargo.duration = embargo_period
                embargo.date_started = datetime.now()
                embargo.date_ended = embargo.date_started + timedelta(
                    weeks=duration_in_weeks
                )
            embargo.save()
    elif embargo_period == "none":
        if Embargo.objects.filter(table=table_obj).exists():
            reset_embargo = Embargo.objects.get(table=table_obj)
            reset_embargo.delete()

    all_peer_reviews = PeerReview.objects.filter(table=table_obj)

    for peer_review in all_peer_reviews:
        peer_review.update_all_table_peer_reviews_after_table_moved(topic=to_schema)

    table_obj.set_is_published(topic_name=to_schema)


def connect():
    engine = _get_engine()
    insp = inspect(engine)
    return insp


def get_table_oid(request: dict, context=None):
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.get_table_oid(
            conn,
            get_or_403(request, "table"),
            schema=request.get("schema", SCHEMA_DEFAULT_TEST_SANDBOX),
            **request,
        )
    except NoSuchTableError as e:
        raise ConnectionError(str(e))
    finally:
        conn.close()
    return result


def close_all_connections(request: dict, context):
    close_all_for_user(request)
    return __response_success()


def fetchall(context: dict):
    cursor = load_cursor_from_context(context)
    return cursor.fetchall()


def fetchmany(request: dict, context):
    cursor = load_cursor_from_context(context)
    return cursor.fetchmany(int(request["size"]))


def getValue(schema, table: str, column, id):
    sql = 'SELECT {column} FROM "{schema}"."{table}" WHERE id={id}'.format(
        column=column, schema=schema, table=table, id=id
    )

    engine = _get_engine()
    session = sessionmaker(bind=engine)()

    try:
        result = session_execute(session, sql)

        returnValue = None
        for row in result:
            returnValue = row[column]

        return returnValue
    except Exception as e:
        logger.error("SQL Action failed. \n Error:\n" + str(e))
        session.rollback()
    finally:
        session.close()
    return None


def apply_changes(schema: str, table: str, cursor: AbstractCursor | None = None):
    """Apply changes from the meta tables to the actual table.

    Meta tables are :
    * _<NAME>_insert
    * _<NAME>_update
    * _<NAME>_delete

    """

    def add_type(d, type):
        d["_type"] = type
        return d

    engine = _get_engine()

    artificial_connection = False
    connection: DBAPIConnection = engine.raw_connection()  # type:ignore TODO

    if cursor is None:
        artificial_connection = True
        cursor = cast(AbstractCursor, connection.cursor())  # type:ignore TODO

    try:

        columns = list(describe_columns(schema, table).keys())
        extended_columns = columns + ["_submitted", "_id"]

        # TODO:permission check is still done outside of this function,
        # so we pass user=None
        oedb_table = Table.objects.get(name=table).get_oeb_table_proxy(user=None)

        insert_sa_table = oedb_table._insert_table.get_sa_table()
        cursor_execute(
            cursor,
            "select * "
            'from "{schema}"."{table}" '
            "where _applied = FALSE;".format(
                schema=insert_sa_table.schema, table=insert_sa_table.name
            ),
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

        update_sa_table = oedb_table._edit_table.get_sa_table()
        cursor_execute(
            cursor,
            "select * "
            'from "{schema}"."{table}" '
            "where _applied = FALSE;".format(
                schema=update_sa_table.schema, table=update_sa_table.name
            ),
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

        delete_sa_table = oedb_table._delete_table.get_sa_table()
        cursor_execute(
            cursor,
            "select * "
            'from "{schema}"."{table}" '
            "where _applied = FALSE;".format(
                schema=delete_sa_table.schema, table=delete_sa_table.name
            ),
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
        sa_table = SATable(table, MetaData(bind=engine), autoload=True, schema=schema)

        # ToDo: This may require some kind of dependency tree resolution
        prev_type = None
        change_batch = []
        for change in sorted(changes, key=lambda x: x["_submitted"]):
            distilled_change = {k: v for k, v in change.items() if k in columns}
            if prev_type and change["_type"] != prev_type:
                _apply_stack(cursor, sa_table, change_batch, prev_type)
                change_batch = []
            else:
                change_batch.append((distilled_change, change["_id"]))
            prev_type = change["_type"]
        if prev_type:
            _apply_stack(cursor, sa_table, change_batch, prev_type)
        if artificial_connection:
            connection.commit()
    except Exception:
        if artificial_connection:
            connection.rollback()
        raise
    finally:
        if artificial_connection:
            cursor.close()
            connection.close()


def _apply_stack(cursor: AbstractCursor, sa_table: SATable, changes, change_type):
    distilled_change, rids = zip(*changes)
    if change_type == "insert":
        apply_insert(cursor, sa_table, distilled_change, rids)
    elif change_type == "update":
        apply_update(cursor, sa_table, distilled_change, rids)
    elif change_type == "delete":
        apply_deletion(cursor, sa_table, distilled_change, rids)


def set_applied(session: AbstractCursor | Session, sa_table: SATable, rids, mode: int):

    # TODO:permission check is still done outside of this function,
    # so we pass user=None
    oedb_table = Table.objects.get(name=sa_table.name).get_oeb_table_proxy(user=None)

    if mode == __INSERT:
        meta_sa_table = oedb_table._insert_table.get_sa_table()
    elif mode == __DELETE:
        meta_sa_table = oedb_table._delete_table.get_sa_table()
    elif mode == __UPDATE:
        meta_sa_table = oedb_table._edit_table.get_sa_table()
    else:
        raise NotImplementedError

    update_query = (
        meta_sa_table.update()
        .where(sql.or_(*(meta_sa_table.c._id == i for i in rids)))
        .values(_applied=True)
        .compile()
    )
    session_execute_parameter(session, str(update_query), update_query.params)


def apply_insert(session: AbstractCursor | Session, sa_table: SATable, rows, rids):
    logger.debug("apply inserts (%d)", len(rids))
    query = sa_table.insert().values(rows)
    _execute_sqla(query, session)
    set_applied(session, sa_table, rids, __INSERT)


def apply_update(session: AbstractCursor | Session, sa_table, rows, rids):
    logger.debug("apply updates (%d)", len(rids))
    for row, rid in zip(rows, rids):
        pks = [c.name for c in sa_table.columns if c.primary_key]
        query = sa_table.update(
            *[getattr(sa_table.c, pk) == row[pk] for pk in pks]
        ).values(row)
        _execute_sqla(query, session)
        set_applied(session, sa_table, [rid], __UPDATE)


def apply_deletion(session: AbstractCursor | Session, sa_table: SATable, rows, rids):
    logger.debug("apply deletion (%d)", len(rids))
    for row, rid in zip(rows, rids):
        query = sa_table.delete().where(
            *[getattr(sa_table.c, col) == row[col] for col in row]
        )
        _execute_sqla(query, session)
        set_applied(session, sa_table, [rid], __DELETE)


def update_meta_search(table: str) -> None:
    """
    TODO: also update JSONB index fields
    """
    table_obj = Table.objects.get(name=table)
    comment = str(dataedit.metadata.load_metadata_from_db(table=table))
    tags = [t.name for t in table_obj.tags.all()]
    s = " ".join(
        (
            *re.findall(r"\w+", table),
            *re.findall(r"\w+", comment),
            *(tag for tag in tags),
        )
    )

    table_obj.search = Func(Value(s), function="to_tsvector")
    table_obj.save()


def set_table_metadata(table: str, metadata):
    """saves metadata as json string on table comment.

    Args:
        table(str): name of table
        metadata: OEPMetadata or metadata object (dict) or metadata str
        cursor: sql alchemy connection cursor
    """

    # ---------------------------------------
    # metadata parsing
    # ---------------------------------------

    # parse the metadata object (various types) into proper OEPMetadata instance
    metadata_oep, err = try_parse_metadata(metadata)
    if err:
        raise APIError(err)
    metadata_oep = metadata_oep or {}
    # compile OEPMetadata instance back into native python object (dict)
    # TODO: we should try to convert to the latest standard in this step?
    metadata_obj, err = try_validate_metadata(metadata_oep)
    if err:
        raise APIError(err)

    # ---------------------------------------
    # update the oemetadata field (JSONB) in django db
    # ---------------------------------------

    django_table_obj = Table.objects.get(name=table)
    django_table_obj.oemetadata = metadata_obj  # type:ignore
    django_table_obj.save()

    # ---------------------------------------
    # update the table human readable name after oemetadata is available
    # ---------------------------------------

    readable_table_name = django_table_obj.get_readable_table_name()
    django_table_obj.set_human_readable_name(
        current_name=django_table_obj.human_readable_name,
        readable_table_name=readable_table_name,
    )

    # ---------------------------------------
    # update search index
    # ---------------------------------------

    update_meta_search(table=table)


def get_single_table_size(table: str) -> dict | None:
    """
    Return size details for one schema.table or None if not found.
    """

    sql = text(
        """
        SELECT
            :schema AS table_schema,
            :table  AS table_name,
            pg_relation_size(format('%I.%I', :schema, :table))                       AS table_bytes,
            pg_indexes_size(format('%I.%I', :schema, :table))                        AS index_bytes,
            pg_total_relation_size(format('%I.%I', :schema, :table))                 AS total_bytes,
            pg_size_pretty(pg_relation_size(format('%I.%I', :schema, :table)))       AS table_pretty,
            pg_size_pretty(pg_indexes_size(format('%I.%I', :schema, :table)))        AS index_pretty,
            pg_size_pretty(pg_total_relation_size(format('%I.%I', :schema, :table))) AS total_pretty
    """  # noqa: E501
    )

    schema = Table.load(name=table).oedb_schema
    sess = _create_oedb_session()
    try:
        res = session_execute_parameter(sess, sql, {"schema": schema, "table": table})
        row = res.fetchone()
        if not row:
            return None
        d = dict(row.items())  # RowProxy -> dict
        for k in ("table_bytes", "index_bytes", "total_bytes"):
            d[k] = int(d[k])
        return d
    finally:
        sess.close()


def list_table_sizes() -> list[dict]:
    """
    List table sizes
    """
    oedb_schema = SCHEMA_DATA
    sql = text(
        f"""
        SELECT
            table_schema,
            table_name,
            pg_relation_size(format('%I.%I', table_schema, table_name))       AS table_bytes,
            pg_indexes_size(format('%I.%I', table_schema, table_name))        AS index_bytes,
            pg_total_relation_size(format('%I.%I', table_schema, table_name)) AS total_bytes,
            pg_size_pretty(pg_total_relation_size(format('%I.%I', table_schema, table_name))) AS total_pretty
        FROM information_schema.tables
        WHERE table_schema='{oedb_schema}'
          AND table_type = 'BASE TABLE'
        ORDER BY pg_total_relation_size(format('%I.%I', table_schema, table_name)) DESC
    """  # noqa: E501
    )

    sess = _create_oedb_session()
    try:
        res = session_execute(sess, sql)
        rows = res.fetchall() or []
        out = []
        for r in rows:
            m = dict(r.items())  # RowProxy -> dict
            for k in ("table_bytes", "index_bytes", "total_bytes"):
                m[k] = int(m[k])
            out.append(m)
        return out
    finally:
        sess.close()


def table_get_approx_row_count(table: Table, precise_below: int = 0) -> int:
    """Get approximate number of rows quickly.

    Especially for huge tables, count(*) is slow,
    so we use reltuples.
    See https://www.postgresql.org/docs/current/catalog-pg-class.html
    This is useful for data preview in frontend, where its not a problem that actual
    number of rows is different because its paginated anywayss.
    See issue #1531
    """

    engine = _get_engine()
    # NOTE: cannot use :parameter, because we insert
    # table / schema name. but its validated by constraints
    # on django table.name field

    query = text(
        f"""
        SELECT reltuples::bigint AS approx_row_count
        FROM pg_class
        WHERE oid = '"{table.oedb_schema}"."{table.name}"'::regclass
        ;
    """
    )

    with engine.connect() as conn:
        resp = connection_execute(conn, query)
        row = resp.fetchone()
        row_count = row[0] if row else 0

    print(row_count, precise_below)
    if row_count >= precise_below:
        return row_count

    query = text(
        f"""
        SELECT count(*)
        FROM "{table.oedb_schema}"."{table.name}"
        ;
    """
    )

    with engine.connect() as conn:
        resp = connection_execute(conn, query)
        row = resp.fetchone()
        row_count = row[0] if row else 0

    return row_count


# -------------------------------------------------------------------------------------
# advanced api: functions will be wrapped in create_ajax_handler
#
# all functions must accept (request: dict, context: dict), but may have
# additional kwargs
#
# -------------------------------------------------------------------------------------


def data_search(request: dict, context: dict | None = None) -> dict:
    query = parse_select(request)
    cursor = load_cursor_from_context(context or {})
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


def data_insert(request: dict, context: dict) -> dict:

    cursor = load_cursor_from_context(context)
    # If the insert request is not for a meta table, change the request to do so
    table_name = get_or_403(request, "table")
    if table_name.startswith("_") or table_name.endswith("_cor"):
        raise APIError("Insertions on meta tables is not allowed", status=403)
    schema_name = request.get("schema", SCHEMA_DEFAULT_TEST_SANDBOX)

    schema_name, table_name = get_table_name(schema_name, table_name)

    assert_permission(user=context["user"], table=table_name, permission=WRITE_PERM)

    # TODO:permission check is still done outside of this function,
    # so we pass user=None
    table_obj = Table.objects.get(name=table_name)
    insert_sa_table = table_obj.get_oeb_table_proxy()._insert_table.get_sa_table()

    request["table"] = insert_sa_table.name
    request["schema"] = insert_sa_table.schema

    query, values = parse_insert(request, context)
    data_insert_check(schema_name, table_name, values, context)
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

    apply_changes(schema_name, table_name, cursor)

    return response


def data_delete(request: dict, context: dict) -> dict:
    orig_table = get_or_403(request, "table")
    if orig_table.startswith("_") or orig_table.endswith("_cor"):
        raise APIError("Insertions on meta tables is not allowed", status=403)
    orig_schema = request.get("schema", SCHEMA_DEFAULT_TEST_SANDBOX)

    schema, table = get_table_name(orig_schema, orig_table)

    if schema is None:
        schema = SCHEMA_DEFAULT_TEST_SANDBOX

    assert_permission(user=context["user"], table=table, permission=DELETE_PERM)

    # TODO:permission check is still done outside of this function,
    # so we pass user=None
    target_meta_sa_table = (
        Table.objects.get(name=orig_table)
        .get_oeb_table_proxy(user=None)
        ._delete_table.get_sa_table()
    )
    setter = []
    cursor = load_cursor_from_context(context)

    drop_not_null_constraints_from_delete_meta_table(
        target_meta_sa_table.name, target_meta_sa_table.schema
    )

    result = __change_rows(request, context, target_meta_sa_table, setter, ["id"])
    apply_changes(schema, table, cursor)
    return result


def data_update(request: dict, context: dict) -> dict:
    orig_table = read_pgid(get_or_403(request, "table"))
    if orig_table.startswith("_") or orig_table.endswith("_cor"):
        raise APIError("Insertions on meta tables is not allowed", status=403)
    orig_schema = read_pgid(request.get("schema", SCHEMA_DEFAULT_TEST_SANDBOX))
    schema, table = get_table_name(orig_schema, orig_table)

    if schema is None:
        schema = SCHEMA_DEFAULT_TEST_SANDBOX

    assert_permission(user=context["user"], table=table, permission=WRITE_PERM)

    # TODO:permission check is still done outside of this function,
    # so we pass user=None
    target_sa_table = (
        Table.objects.get(name=orig_table)
        .get_oeb_table_proxy(user=None)
        ._edit_table.get_sa_table()
    )
    setter = get_or_403(request, "values")
    if isinstance(setter, list):
        if "fields" not in request:
            raise APIError("values passed in list format without field info")
        field_names = [read_pgid(d["column"]) for d in request["fields"]]
        setter = dict(zip(field_names, setter))
    cursor = load_cursor_from_context(context)  # TODO:
    result = __change_rows(request, context, target_sa_table, setter)
    apply_changes(schema, table, cursor)
    return result


def data_info(request: dict, context: dict | None = None) -> dict:
    return request


def has_schema(request: dict, context: dict | None = None) -> bool:
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.has_schema(conn, get_or_403(request, "schema"))
    finally:
        conn.close()
    return bool(result)


def has_table(request: dict, context: dict | None = None) -> bool:
    table = get_or_403(request, "table")
    return Table.objects.filter(name=table).exists()


def has_sequence(request: dict, context: dict | None = None) -> bool:
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.has_sequence(
            conn,
            get_or_403(request, "sequence_name"),
            schema=request.get("schema", SCHEMA_DEFAULT_TEST_SANDBOX),
        )
    finally:
        conn.close()
    return result


def has_type(request: dict, context: dict | None = None) -> bool:
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.has_schema(
            conn,
            get_or_403(request, "sequence_name"),
            schema=request.get("schema", SCHEMA_DEFAULT_TEST_SANDBOX),
        )
    finally:
        conn.close()
    return result


def get_schema_names(request: dict, context: dict | None = None) -> dict:
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.get_schema_names(engine.connect(), **request)
    finally:
        conn.close()
    return result


def get_table_names(request: dict, context: dict | None = None) -> dict:
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.get_table_names(
            conn, schema=request.pop("schema", SCHEMA_DEFAULT_TEST_SANDBOX), **request
        )
    finally:
        conn.close()
    return result


def get_view_names(request: dict, context: dict | None = None) -> dict:
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.get_view_names(
            conn, schema=request.pop("schema", SCHEMA_DEFAULT_TEST_SANDBOX), **request
        )
    finally:
        conn.close()
    return result


def get_view_definition(request: dict, context: dict | None = None) -> dict:
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.get_schema_names(
            conn,
            get_or_403(request, "view_name"),
            schema=request.pop("schema", SCHEMA_DEFAULT_TEST_SANDBOX),
            **request,
        )
    finally:
        conn.close()
    return result


def get_columns(request: dict, context: dict | None = None) -> dict:
    engine = _get_engine()
    connection: Connection = engine.connect()

    table_name = get_or_403(request, "table")
    schema = request.pop("schema", SCHEMA_DEFAULT_TEST_SANDBOX)
    schema = validate_schema(schema)

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
    except NoSuchTableError as e:
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
    c = connection_execute(connection, s, table_oid=table_oid)
    rows = c.fetchall() or []

    domains = engine.dialect._load_domains(connection)

    enums = dict(
        (
            (
                "%s.%s" % (rec["schema"], rec["name"])
                if not rec["visible"]
                else rec["name"]
            ),
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


def get_pk_constraint(request: dict, context: dict | None = None) -> dict:
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.get_pk_constraint(
            conn,
            get_or_403(request, "table"),
            schema=request.pop("schema", SCHEMA_DEFAULT_TEST_SANDBOX),
            **request,
        )
    finally:
        conn.close()
    return result


def get_foreign_keys(request: dict, context: dict | None = None) -> dict:
    engine = _get_engine()
    conn = engine.connect()
    if not request.get("schema", None):
        request["schema"] = SCHEMA_DEFAULT_TEST_SANDBOX
    try:
        result = engine.dialect.get_foreign_keys(
            conn,
            get_or_403(request, "table"),
            postgresql_ignore_search_path=request.pop(
                "postgresql_ignore_search_path", False
            ),
            **request,
        )
    finally:
        conn.close()
    return result


def get_indexes(request: dict, context: dict | None = None) -> dict:
    engine = _get_engine()
    conn = engine.connect()
    if not request.get("schema", None):
        request["schema"] = SCHEMA_DEFAULT_TEST_SANDBOX
    try:
        result = engine.dialect.get_indexes(
            conn, get_or_403(request, "table"), **request
        )
    finally:
        conn.close()
    return result


def get_unique_constraints(request: dict, context: dict | None = None) -> dict:
    engine = _get_engine()
    conn = engine.connect()
    if not request.get("schema", None):
        request["schema"] = SCHEMA_DEFAULT_TEST_SANDBOX
    try:
        result = engine.dialect.get_foreign_keys(
            conn, get_or_403(request, "table"), **request
        )
    finally:
        conn.close()
    return result


def get_isolation_level(request: dict, context: dict) -> dict:
    engine = _get_engine()
    cursor = load_cursor_from_context(context)
    result = engine.dialect.get_isolation_level(cursor)
    return result


def set_isolation_level(request: dict, context: dict) -> dict:
    level = request.get("level", None)
    engine = _get_engine()
    cursor = load_cursor_from_context(context)
    try:
        engine.dialect.set_isolation_level(cursor, level)
    except exc.ArgumentError as ae:
        return _response_error(str(ae))
    return __response_success()


def do_begin_twophase(request: dict, context: dict) -> dict:
    xid = request.get("xid", None)
    engine = _get_engine()
    cursor = load_cursor_from_context(context)
    engine.dialect.do_begin_twophase(cursor, xid)
    return __response_success()


def do_prepare_twophase(request: dict, context: dict) -> dict:
    xid = request.get("xid", None)
    engine = _get_engine()
    cursor = load_cursor_from_context(context)
    engine.dialect.do_prepare_twophase(cursor, xid)
    return __response_success()


def do_rollback_twophase(request: dict, context: dict) -> dict:
    xid = request.get("xid", None)
    is_prepared = request.get("is_prepared", True)
    recover = request.get("recover", False)
    engine = _get_engine()
    cursor = load_cursor_from_context(context)
    engine.dialect.do_rollback_twophase(
        cursor, xid, is_prepared=is_prepared, recover=recover
    )
    return __response_success()


def do_commit_twophase(request: dict, context: dict) -> dict:
    xid = request.get("xid", None)
    is_prepared = request.get("is_prepared", True)
    recover = request.get("recover", False)
    engine = _get_engine()
    cursor = load_cursor_from_context(context)
    engine.dialect.do_commit_twophase(
        cursor, xid, is_prepared=is_prepared, recover=recover
    )
    return __response_success()


def do_recover_twophase(request: dict, context: dict) -> dict:
    engine = _get_engine()
    cursor = load_cursor_from_context(context)
    return engine.dialect.do_commit_twophase(cursor)


def open_raw_connection(request: dict, context: dict) -> dict:
    session_context = SessionContext(owner=context.get("user"))
    return {"connection_id": session_context.connection._id}


def commit_raw_connection(request: dict, context: dict) -> dict:
    connection = load_session_from_context(context).connection
    connection.commit()
    return __response_success()


def rollback_raw_connection(request: dict, context: dict) -> dict:
    load_session_from_context(context).rollback()
    return __response_success()


def close_raw_connection(request: dict, context: dict) -> dict:
    load_session_from_context(context).close()
    return __response_success()


def open_cursor(request: dict, context: dict, named: bool = False) -> dict:
    session_context = load_session_from_context(context)
    cursor_id = session_context.open_cursor(named=named)
    return {"cursor_id": cursor_id}


def close_cursor(request: dict, context: dict) -> dict:
    session_context = load_session_from_context(context)
    cursor_id = int(context["cursor_id"])
    session_context.close_cursor(cursor_id)
    return {"cursor_id": cursor_id}


def fetchone(request: dict, context: dict) -> list | None:
    cursor = load_cursor_from_context(context)
    row = cursor.fetchone()
    if row:
        row = [_translate_fetched_cell(cell) for cell in row]
        return row
    else:
        return row


# -------------------------------------------------------------------------------------
# temporarily extracted functions doing sqlalchemy execute
# -------------------------------------------------------------------------------------


def session_execute(session: Session, sql) -> ResultProxy:
    response = session.execute(sql)
    # Note: cast is only for type checking,
    # should disappear once we migrate to sqlalchemy >= 1.4
    response = cast(ResultProxy, response)
    return response


def session_execute_parameter(
    session: AbstractCursor | Session, sql, parameter
) -> ResultProxy:
    response = session.execute(sql, parameter)
    # Note: cast is only for type checking,
    # should disappear once we migrate to sqlalchemy >= 1.4
    response = cast(ResultProxy, response)
    return response


def engine_execute(engine: Engine, sql) -> ResultProxy:
    response = engine.execute(sql)
    # Note: cast is only for type checking,
    # should disappear once we migrate to sqlalchemy >= 1.4
    response = cast(ResultProxy, response)
    return response


def connection_execute(connection: Connection, sql, **kwargs) -> ResultProxy:
    response = connection.execute(sql, **kwargs)
    # Note: cast is only for type checking,
    # should disappear once we migrate to sqlalchemy >= 1.4
    response = cast(ResultProxy, response)
    return response


def cursor_execute(cursor: AbstractCursor, sql) -> None:
    cursor.execute(sql)


def cursor_execute_parameter(cursor: AbstractCursor | Session, sql, parameter) -> None:
    cursor.execute(sql, parameter)
