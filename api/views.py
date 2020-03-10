import csv
import itertools
import json
import logging
import re
import time
from decimal import Decimal

import geoalchemy2  # Although this import seems unused is has to be here
import sqlalchemy as sqla
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from rest_framework import status
from rest_framework.views import APIView

import api.parser
import login.models as login_models
from api import actions, parser, sessions
from api.encode import Echo, GeneratorJSONEncoder
from api.error import APIError
from api.helpers.http import ModHttpResponse
from dataedit.models import Table as DBTable
from dataedit.views import load_metadata_from_db, save_metadata_as_table_comment
from oeplatform.securitysettings import PLAYGROUNDS, UNVERSIONED_SCHEMAS

logger = logging.getLogger("oeplatform")

WHERE_EXPRESSION = re.compile(
    "^(?P<first>[\w\d_\.]+)\s*(?P<operator>"
    + "|".join(parser.sql_operators)
    + ")\s*(?P<second>(?![>=]).+)$"
)


def load_cursor(f):
    def wrapper(*args, **kwargs):
        artificial_connection = "connection_id" not in args[1].data
        fetch_all = "cursor_id" not in args[1].data
        if fetch_all:

            # django_restframework passes different data dictionaries depending
            # on the request type: PUT -> Mutable, POST -> Immutable
            # Thus, we have to replace the data dictionary by one we can mutate.
            if hasattr(args[1].data, "_mutable"):
                args[1].data._mutable = True
            context = {}
            context["user"] = args[1].user
            if not artificial_connection:
                context["connection_id"] = args[1].data["connection_id"]
            else:
                context.update(actions.open_raw_connection({}, context))
                args[1].data["connection_id"] = context["connection_id"]
            if "cursor_id" in args[1].data:
                context["cursor_id"] = args[1].data["cursor_id"]
            else:
                context.update(actions.open_cursor({}, context))
                args[1].data["cursor_id"] = context["cursor_id"]
        try:
            result = f(*args, **kwargs)
            if fetch_all:
                cursor = actions.load_cursor_from_context(context)
                session = actions.load_session_from_context(context)
                if not result:
                    result = {}
                if cursor.description:
                    result["description"] = cursor.description
                    result["rowcount"] = cursor.rowcount
                    result["data"] = (
                        list(map(actions._translate_fetched_cell, row))
                        for row in cursor.fetchall()
                    )
                if artificial_connection:
                    session.connection.commit()
        finally:
            if fetch_all:
                actions.close_cursor({}, context)
            if artificial_connection:
                actions.close_raw_connection({}, context)
        return result

    return wrapper


def cors(allow):
    def doublewrapper(f):
        def wrapper(*args, **kwargs):
            response = f(*args, **kwargs)
            if allow:
                response["Access-Control-Allow-Origin"] = "*"
                response["Access-Control-Allow-Methods"] = "POST"
                response["Access-Control-Allow-Headers"] = "Content-Type"
            return response

        return wrapper

    return doublewrapper


def api_exception(f):
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except actions.APIError as e:
            return JsonResponse({"reason": e.message}, status=e.status)
        except KeyError as e:
            return JsonResponse({"reason": e}, status=400)

    return wrapper


def permission_wrapper(permission, f):
    def wrapper(caller, request, *args, **kwargs):
        schema = kwargs.get("schema", actions.DEFAULT_SCHEMA)
        table = kwargs.get("table") or kwargs.get("sequence")
        actions.assert_permission(request.user, table, permission, schema=schema)
        return f(caller, request, *args, **kwargs)

    return wrapper


def require_write_permission(f):
    return permission_wrapper(login_models.WRITE_PERM, f)


def require_delete_permission(f):
    return permission_wrapper(login_models.DELETE_PERM, f)


def require_admin_permission(f):
    return permission_wrapper(login_models.ADMIN_PERM, f)


def conjunction(clauses):
    return {"type": "operator", "operator": "AND", "operands": clauses}


class Sequence(APIView):
    @api_exception
    def put(self, request, schema, sequence):
        if schema not in PLAYGROUNDS and schema not in UNVERSIONED_SCHEMAS:
            raise PermissionDenied
        if schema.startswith("_"):
            raise PermissionDenied
        if request.user.is_anonymous():
            raise PermissionDenied
        if actions.has_sequence(dict(schema=schema, sequence_name=sequence), {}):
            raise APIError("Sequence already exists")
        return self.__create_sequence(request, schema, sequence, request.data)

    @api_exception
    @require_delete_permission
    def delete(self, request, schema, sequence):
        if schema not in PLAYGROUNDS and schema not in UNVERSIONED_SCHEMAS:
            raise PermissionDenied
        if schema.startswith("_"):
            raise PermissionDenied
        if request.user.is_anonymous():
            raise PermissionDenied
        return self.__delete_sequence(request, schema, sequence, request.data)

    @load_cursor
    def __delete_sequence(self, request, schema, sequence, jsn):
        seq = sqla.schema.Sequence(sequence, schema=schema)
        seq.drop(bind=actions._get_engine())
        return JsonResponse({}, status=status.HTTP_200_OK)

    @load_cursor
    def __create_sequence(self, request, schema, sequence, jsn):
        seq = sqla.schema.Sequence(sequence, schema=schema)
        seq.create(bind=actions._get_engine())
        return JsonResponse({}, status=status.HTTP_201_CREATED)


class Table(APIView):
    """
    Handels the creation of tables and serves information on existing tables
    """

    @api_exception
    def get(self, request, schema, table):
        """
        Returns a dictionary that describes the DDL-make-up of this table.
        Fields are:

        * name : Name of the table,
        * schema: Name of the schema,
        * columns : as specified in :meth:`api.actions.describe_columns`
        * indexes : as specified in :meth:`api.actions.describe_indexes`
        * constraints: as specified in
                    :meth:`api.actions.describe_constraints`

        :param request:
        :return:
        """

        schema, table = actions.get_table_name(schema, table, restrict_schemas=False)

        return JsonResponse(
            {
                "schema": schema,
                "name": table,
                "columns": actions.describe_columns(schema, table),
                "indexed": actions.describe_indexes(schema, table),
                "constraints": actions.describe_constraints(schema, table),
            }
        )

    @api_exception
    def post(self, request, schema, table):
        """
        Changes properties of tables and table columns
        :param request:
        :param schema:
        :param table:
        :return:
        """
        if schema not in PLAYGROUNDS and schema not in UNVERSIONED_SCHEMAS:
            raise PermissionDenied
        if schema.startswith("_"):
            raise PermissionDenied
        json_data = request.data

        if "column" in json_data["type"]:

            column_definition = api.parser.parse_scolumnd_from_columnd(
                schema, table, json_data["name"], json_data
            )
            result = actions.queue_column_change(schema, table, column_definition)
            return ModHttpResponse(result)

        elif "constraint" in json_data["type"]:

            # Input has nothing to do with DDL from Postgres.
            # Input is completely different.
            # Using actions.parse_sconstd_from_constd is not applicable
            # dict.get() returns None, if key does not exist
            constraint_definition = {
                "action": json_data["action"],  # {ADD, DROP}
                "constraint_type": json_data.get(
                    "constraint_type"
                ),  # {FOREIGN KEY, PRIMARY KEY, UNIQUE, CHECK}
                "constraint_name": json_data.get(
                    "constraint_name"
                ),  # {myForeignKey, myUniqueConstraint}
                "constraint_parameter": json_data.get("constraint_parameter"),
                # Things in Brackets, e.g. name of column
                "reference_table": json_data.get("reference_table"),
                "reference_column": json_data.get("reference_column"),
            }

            result = actions.queue_constraint_change(
                schema, table, constraint_definition
            )
            return ModHttpResponse(result)
        else:
            return ModHttpResponse(
                actions.get_response_dict(False, 400, "type not recognised")
            )

    @api_exception
    def put(self, request, schema, table):
        """
        Every request to unsave http methods have to contain a "csrftoken".
        This token is used to deny cross site reference forwarding.
        In every request the header had to contain "X-CSRFToken" with the actual csrftoken.
        The token can be requested at / and will be returned as cookie.

        :param request:
        :return:
        """
        if schema not in PLAYGROUNDS and schema not in UNVERSIONED_SCHEMAS:
            raise PermissionDenied
        if schema.startswith("_"):
            raise PermissionDenied
        if request.user.is_anonymous():
            raise PermissionDenied
        if actions.has_table(dict(schema=schema, table=table), {}):
            raise APIError("Table already exists")
        json_data = request.data["query"]
        constraint_definitions = []
        column_definitions = []

        for constraint_definiton in json_data.get("constraints", []):
            constraint_definiton.update(
                {"action": "ADD", "c_table": table, "c_schema": schema}
            )
            constraint_definitions.append(constraint_definiton)

        if "columns" not in json_data:
            raise actions.APIError("Table contains no columns")
        for column_definition in json_data["columns"]:
            column_definition.update({"c_table": table, "c_schema": schema})
            column_definitions.append(column_definition)

        result = self.__create_table(
            request, schema, table, column_definitions, constraint_definitions
        )

        perm, _ = login_models.UserPermission.objects.get_or_create(
            table=DBTable.load(schema, table), holder=request.user
        )
        perm.level = login_models.ADMIN_PERM
        perm.save()
        request.user.save()
        return JsonResponse({}, status=status.HTTP_201_CREATED)

    def validate_column_names(self, column_definitions):
        """Raise APIError if any column name is invalid"""
        for c in column_definitions:
            colname = c["name"]
            if not colname.isidentifier():
                raise APIError("Invalid column name: %s" % colname)

    @load_cursor
    def __create_table(
        self, request, schema, table, column_definitions, constraint_definitions
    ):
        self.validate_column_names(column_definitions)
        context = {
            "connection_id": actions.get_or_403(request.data, "connection_id"),
            "cursor_id": actions.get_or_403(request.data, "cursor_id"),
        }
        cursor = sessions.load_cursor_from_context(context)
        actions.table_create(
            schema, table, column_definitions, constraint_definitions, cursor
        )

    @api_exception
    @require_delete_permission
    def delete(self, request, schema, table):
        schema, table = actions.get_table_name(schema, table)

        meta_schema = actions.get_meta_schema_name(schema)

        edit_table = actions.get_edit_table_name(schema, table)
        actions._get_engine().execute(
            "DROP TABLE {schema}.{table} CASCADE;".format(
                schema=meta_schema, table=edit_table
            )
        )

        edit_table = actions.get_insert_table_name(schema, table)
        actions._get_engine().execute(
            "DROP TABLE {schema}.{table} CASCADE;".format(
                schema=meta_schema, table=edit_table
            )
        )

        edit_table = actions.get_delete_table_name(schema, table)
        actions._get_engine().execute(
            "DROP TABLE {schema}.{table} CASCADE;".format(
                schema=meta_schema, table=edit_table
            )
        )

        actions._get_engine().execute(
            "DROP TABLE {schema}.{table} CASCADE;".format(schema=schema, table=table)
        )

        return JsonResponse({}, status=status.HTTP_200_OK)


class Index(APIView):
    def get(self, request):
        pass

    def post(self, request):
        pass

    def put(self, request):
        pass


class Column(APIView):
    @api_exception
    def get(self, request, schema, table, column=None):
        schema, table = actions.get_table_name(schema, table, restrict_schemas=False)
        response = actions.describe_columns(schema, table)
        if column:
            try:
                response = response[column]
            except KeyError:
                raise actions.APIError(
                    "The column specified is not part of " "this table."
                )
        return JsonResponse(response)

    @api_exception
    @require_write_permission
    def post(self, request, schema, table, column):
        schema, table = actions.get_table_name(schema, table)
        response = actions.column_alter(
            request.data["query"], {}, schema, table, column
        )
        return JsonResponse(response)

    @api_exception
    @require_write_permission
    def put(self, request, schema, table, column):
        schema, table = actions.get_table_name(schema, table)
        actions.column_add(schema, table, column, request.data["query"])
        return JsonResponse({}, status=201)


class Fields(APIView):
    def get(self, request, schema, table, id, column=None):
        schema, table = actions.get_table_name(schema, table, restrict_schemas=False)
        if (
            not parser.is_pg_qual(table)
            or not parser.is_pg_qual(schema)
            or not parser.is_pg_qual(id)
            or not parser.is_pg_qual(column)
        ):
            return ModHttpResponse({"error": "Bad Request", "http_status": 400})

        returnValue = actions.getValue(schema, table, column, id)

        return HttpResponse(
            returnValue if returnValue is not None else "",
            status=(404 if returnValue is None else 200),
        )

    def post(self, request):
        pass

    def put(self, request):
        pass


def build_csv(header, result_iterator):
    yield b",".join(header)
    yield b"\n"
    for row in result_iterator:
        yield b",".join(b'"' + bytes(cell) + b'"' for cell in row).replace(b'"', b'""')
        yield b"\n"


class Rows(APIView):
    @api_exception
    def get(self, request, schema, table, row_id=None):
        schema, table = actions.get_table_name(schema, table, restrict_schemas=False)
        columns = request.GET.getlist("column")

        where = request.GET.getlist("where")
        if row_id and where:
            raise actions.APIError(
                "Where clauses and row id are not allowed in the same query"
            )

        orderby = request.GET.getlist("orderby")
        if row_id and orderby:
            raise actions.APIError(
                "Order by clauses and row id are not allowed in the same query"
            )

        limit = request.GET.get("limit")
        if row_id and limit:
            raise actions.APIError(
                "Limit by clauses and row id are not allowed in the same query"
            )

        offset = request.GET.get("offset")
        if row_id and offset:
            raise actions.APIError(
                "Order by clauses and row id are not allowed in the same query"
            )

        format = request.GET.get("form")

        if offset is not None and not offset.isdigit():
            raise actions.APIError("Offset must be integer")
        if limit is not None and not limit.isdigit():
            raise actions.APIError("Limit must be integer")
        if not all(parser.is_pg_qual(c) for c in columns):
            raise actions.APIError("Columns are no postgres qualifiers")
        if not all(parser.is_pg_qual(c) for c in orderby):
            raise actions.APIError(
                "Columns in groupby-clause are no postgres qualifiers"
            )

        # OPERATORS could be EQUALS, GREATER, LOWER, NOTEQUAL, NOTGREATER, NOTLOWER
        # CONNECTORS could be AND, OR
        # If you connect two values with an +, it will convert the + to a space. Whatever.

        where_clauses = self.__read_where_clause(where)

        if row_id:
            clause = {
                "operands": [{"type": "column", "column": "id"}, row_id],
                "operator": "EQUALS",
                "type": "operator",
            }
            if where_clauses:
                where_clauses = conjunction(clause, where_clauses)
            else:
                where_clauses = clause

        # TODO: Validate where_clauses. Should not be vulnerable
        data = {
            "schema": schema,
            "table": table,
            "columns": columns,
            "where": where_clauses,
            "orderby": orderby,
            "limit": limit,
            "offset": offset,
        }

        return_obj = self.__get_rows(request, data)
        # Extract column names from description
        cols = [col[0] for col in return_obj["description"]]

        if format == "csv":
            pseudo_buffer = Echo()
            writer = csv.writer(pseudo_buffer, quoting=csv.QUOTE_ALL)
            response = StreamingHttpResponse(
                (
                    writer.writerow(x)
                    for x in itertools.chain([cols], return_obj["data"])
                ),
                content_type="text/csv",
            )
            response[
                "Content-Disposition"
            ] = 'attachment; filename="{schema}__{table}.csv"'.format(
                schema=schema, table=table
            )
            return response

        else:
            if row_id:
                dict_list = [dict(zip(cols, row)) for row in return_obj["data"]]
                if dict_list:
                    dict_list = dict_list[0]
                else:
                    raise Http404
                # TODO: Figure out what JsonResponse does different.
                return JsonResponse(dict_list, safe=False)

            return stream((dict(zip(cols, row)) for row in return_obj["data"]))

    @api_exception
    @require_write_permission
    def post(self, request, schema, table, row_id=None, action=None):
        schema, table = actions.get_table_name(schema, table)
        column_data = request.data["query"]
        status_code = status.HTTP_200_OK
        if row_id:
            response = self.__update_rows(request, schema, table, column_data, row_id)
        else:
            if action == "new":
                response = self.__insert_row(
                    request, schema, table, column_data, row_id
                )
                status_code = status.HTTP_201_CREATED
            else:
                response = self.__update_rows(request, schema, table, column_data, None)
        actions.apply_changes(schema, table)
        return stream(response, status_code=status_code)

    @api_exception
    @require_write_permission
    def put(self, request, schema, table, row_id=None, action=None):
        if action:
            raise APIError(
                "This request type (PUT) is not supported. The "
                "'new' statement is only possible in POST requests."
            )
        schema, table = actions.get_table_name(schema, table)
        if not row_id:
            return JsonResponse(
                actions._response_error("This methods requires an id"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        column_data = request.data["query"]

        if row_id and column_data.get("id", int(row_id)) != int(row_id):
            raise actions.APIError(
                "Id in URL and query do not match. Ids may not change.",
                status=status.HTTP_409_CONFLICT,
            )

        engine = actions._get_engine()
        # check whether id is already in use
        exists = (
            engine.execute(
                "select count(*) "
                "from {schema}.{table} "
                "where id = {id};".format(schema=schema, table=table, id=row_id)
            ).first()[0]
            > 0
            if row_id
            else False
        )
        if exists:
            response = self.__update_rows(request, schema, table, column_data, row_id)
            actions.apply_changes(schema, table)
            return JsonResponse(response)
        else:
            result = self.__insert_row(request, schema, table, column_data, row_id)
            actions.apply_changes(schema, table)
            return JsonResponse(result, status=status.HTTP_201_CREATED)

    @require_delete_permission
    def delete(self, request, table, schema, row_id=None):
        schema, table = actions.get_table_name(schema, table)
        result = self.__delete_rows(request, schema, table, row_id)
        actions.apply_changes(schema, table)
        return JsonResponse(result)

    @load_cursor
    def __delete_rows(self, request, schema, table, row_id=None):
        where = request.GET.getlist("where")
        query = {"schema": schema, "table": table}
        if where:
            query["where"] = self.__read_where_clause(where)
        context = {
            "connection_id": request.data["connection_id"],
            "cursor_id": request.data["cursor_id"],
            "user": request.user,
        }

        if row_id:
            clause = {
                "operator": "=",
                "operands": [
                    actions._load_value(row_id),
                    {"type": "column", "column": "id"},
                ],
                "type": "operator",
            }
            where = query.get("where")
            if where:  # If there is already a where clause take the conjunction
                clause = conjunction([clause, where])
            query["where"] = clause

        return actions.data_delete(query, context)

    def __read_where_clause(self, wheres):
        where_clauses = []
        if wheres:
            for where in wheres:
                if where:
                    where_splitted = re.findall(WHERE_EXPRESSION, where)
                    where_clauses.append(
                        conjunction(
                            [
                                {
                                    "operands": [
                                        {"type": "column", "column": match[0]},
                                        match[2],
                                    ],
                                    "operator": match[1],
                                    "type": "operator",
                                }
                                for match in where_splitted
                            ]
                        )
                    )
        return where_clauses

    @load_cursor
    def __insert_row(self, request, schema, table, row, row_id=None):
        if row_id and row.get("id", int(row_id)) != int(row_id):
            return actions._response_error(
                "The id given in the query does not " "match the id given in the url"
            )
        if row_id:
            row["id"] = row_id

        context = {
            "connection_id": request.data["connection_id"],
            "cursor_id": request.data["cursor_id"],
            "user": request.user,
        }

        query = {
            "schema": schema,
            "table": table,
            "values": [row] if isinstance(row, dict) else row,
        }

        if not row_id:
            query["returning"] = [{"type": "column", "column": "id"}]
        result = actions.data_insert(query, context)

        return result

    @load_cursor
    def __update_rows(self, request, schema, table, row, row_id=None):
        context = {
            "connection_id": request.data["connection_id"],
            "cursor_id": request.data["cursor_id"],
            "user": request.user,
        }

        where = request.GET.getlist("where")

        query = {"schema": schema, "table": table, "values": row}

        if where:
            query["where"] = self.__read_where_clause(where)

        if row_id:
            clause = {
                "operator": "=",
                "operands": [
                    actions._load_value(row_id),
                    {"type": "column", "column": "id"},
                ],
                "type": "operator",
            }
            where = query.get("where")
            if where:
                clause = conjunction([clause, where])
            query["where"] = clause

        return actions.data_update(query, context)

    @load_cursor
    def __get_rows(self, request, data):
        table = actions._get_table(data["schema"], table=data["table"])
        params = {}
        params_count = 0
        columns = data.get("columns")

        if not columns:
            query = table.select()
        else:
            columns = [actions.get_column_obj(table, c) for c in columns]
            query = sqla.select(columns=columns)

        where_clauses = data.get("where")

        if where_clauses:
            query = query.where(parser.parse_condition(where_clauses))

        orderby = data.get("orderby")
        if orderby:
            if isinstance(orderby, list):
                query = query.order_by(*map(parser.parse_expression, orderby))
            elif isinstance(orderby, str):
                query = query.order_by(orderby)
            else:
                raise APIError("Unknown order_by clause: " + orderby)

        limit = data.get("limit")
        if limit and limit.isdigit():
            query = query.limit(int(limit))

        offset = data.get("offset")
        if offset and offset.isdigit():
            query = query.offset(int(offset))

        cursor = sessions.load_cursor_from_context(request.data)
        actions._execute_sqla(query, cursor)


class Metadata(APIView):
    @api_exception
    def get(self, request, schema, table):
        schema, table = actions.get_table_name(schema, table, restrict_schemas=False)
        metadata = load_metadata_from_db(schema=schema, table=table)
        response = {'metadata': metadata}
        return stream(data=response)

    @api_exception
    @require_write_permission
    def post(self, request, schema, table):
        schema, table = actions.get_table_name(schema, table, restrict_schemas=False)
        metadata = request.data['metadata']
        save_metadata_as_table_comment(schema=schema, table=table, metadata=metadata)
        response = {'status': 'ok'}
        return stream(data=response)

class Session(APIView):
    def get(self, request, length=1):
        return request.session["resonse"]


def date_handler(obj):
    """
    Implements a handler to serialize dates in JSON-strings
    :param obj: An object
    :return: The str method is called (which is the default serializer for JSON) unless the object has an attribute  *isoformat*
    """
    if isinstance(obj, Decimal):
        return str(obj)
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    else:
        return str(obj)


# Create your views here.


def create_ajax_handler(func, allow_cors=False, requires_cursor=False):
    """
    Implements a mapper from api pages to the corresponding functions in
    api/actions.py
    :param func: The name of the callable function
    :return: A JSON-Response that contains a dictionary with the corresponding response stored in *content*
    """

    class AJAX_View(APIView):
        @cors(allow_cors)
        @api_exception
        def options(self, request, *args, **kwargs):
            response = HttpResponse()

            return response

        @cors(allow_cors)
        @api_exception
        def post(self, request):
            result = self.execute(request)
            return stream(result, allow_cors=allow_cors and request.user.is_anonymous)

        def execute(self, request):
            if requires_cursor:
                return load_cursor(self._internal_execute)(self, request)
            else:
                return self._internal_execute(request, request)

        def _internal_execute(self, *args):
            request = args[1]
            content = request.data
            context = {"user": request.user}
            if "cursor_id" in request.data:
                context["cursor_id"] = request.data["cursor_id"]
            if "connection_id" in request.data:
                context["connection_id"] = request.data["connection_id"]
            query = content.get("query", ["{}"])
            try:
                if isinstance(query, list):
                    query = query[0]
                if isinstance(query, str):
                    query = json.loads(query)
            except:
                raise APIError("Your query is not properly formated.")
            data = func(query, context)

            # This must be done in order to clean the structure of non-serializable
            # objects (e.g. datetime)
            if isinstance(data, dict) and "domains" in data:
                data["domains"] = {
                    (".".join(key) if isinstance(key, tuple) else key): val
                    for key, val in data["domains"].items()
                }
            response_data = json.loads(json.dumps(data, default=date_handler))

            result = {"content": response_data}

            if "cursor_id" in context:
                result["cursor_id"] = context["cursor_id"]

            return result

    return AJAX_View.as_view()


class FetchView(APIView):
    @api_exception
    def post(self, request, fetchtype):
        if fetchtype == "all":
            return self.do_fetch(request, actions.fetchall)
        elif fetchtype == "many":
            return self.do_fetch(request, actions.fetchmany)
        else:
            raise APIError("Unknown fetchtype: %s" % fetchtype)

    def do_fetch(self, request, fetch):
        context = {
            "connection_id": actions.get_or_403(request.data, "connection_id"),
            "cursor_id": actions.get_or_403(request.data, "cursor_id"),
            "user": request.user,
        }
        return StreamingHttpResponse(
            (
                part
                for row in fetch(context)
                for part in (self.transform_row(row), "\n")
            ),
            content_type="application/json",
        )

    def transform_row(self, row):
        return json.dumps(
            [actions._translate_fetched_cell(cell) for cell in row],
            default=date_handler,
        )


def stream(data, allow_cors=False, status_code=status.HTTP_200_OK):
    encoder = GeneratorJSONEncoder()
    response = StreamingHttpResponse(
        encoder.iterencode(data), content_type="application/json", status=status_code
    )
    if allow_cors:
        response["Access-Control-Allow-Origin"] = "*"
    return response


class CloseAll(LoginRequiredMixin, APIView):
    def get(self, request):
        sessions.close_all_for_user(request.user)
        return HttpResponse("All connections closed")


def get_users(request):
    string = request.GET["name"]
    users = login_models.myuser.objects.filter(
        Q(name__trigram_similar=string) | Q(name__istartswith=string)
    )
    return JsonResponse([user.name for user in users], safe=False)


def get_groups(request):
    string = request.GET["name"]
    users = login_models.Group.objects.filter(
        Q(name__trigram_similar=string) | Q(name__istartswith=string)
    )
    return JsonResponse([user.name for user in users], safe=False)
