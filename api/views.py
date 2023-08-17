import csv
import itertools
import json
import logging
import re
from decimal import Decimal

import geoalchemy2  # noqa: Although this import seems unused is has to be here
import psycopg2
import requests
import sqlalchemy as sqla
import zipstream
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db.utils import IntegrityError
from django.http import Http404, HttpResponse, JsonResponse, StreamingHttpResponse
from omi.dialects.oep.compiler import JSONCompiler
from omi.structure import OEPMetadata
from rest_framework import status
from rest_framework.views import APIView

import api.parser
import login.models as login_models
from api import actions, parser, sessions
from api.encode import Echo, GeneratorJSONEncoder
from api.error import APIError
from api.helpers.http import ModHttpResponse
from dataedit.models import Table as DBTable
from dataedit.models import Topic
from dataedit.views import get_tag_keywords_synchronized_metadata
from oeplatform.settings import (
    DATASET_SCHEMA,
    DEFAULT_SCHEMA,
    DRAFT_SCHEMA,
    EDITABLE_SCHEMAS,
)

logger = logging.getLogger("oeplatform")

MAX_COL_NAME_LENGTH = 50

WHERE_EXPRESSION = re.compile(
    r"^(?P<first>[\w\d_\.]+)\s*(?P<operator>"
    + r"|".join(parser.sql_operators)
    + r")\s*(?P<second>(?![>=]).+)$"
)


def transform_results(cursor, triggers, trigger_args):
    row = cursor.fetchone() if not cursor.closed else None
    while row is not None:
        yield list(map(actions._translate_fetched_cell, row))
        row = cursor.fetchone()
    for t, targs in zip(triggers, trigger_args):
        t(*targs)


class OEPStream(StreamingHttpResponse):
    def __init__(self, *args, session=None, **kwargs):
        self.session = session
        super(OEPStream, self).__init__(*args, **kwargs)

    def __del__(self):
        if self.session:
            self.session.close()


def load_cursor(named=False):
    def inner(f):
        def wrapper(*args, **kwargs):
            artificial_connection = "connection_id" not in args[1].data
            fetch_all = "cursor_id" not in args[1].data
            triggered_close = False
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
                    context.update(actions.open_cursor({}, context, named=named))
                    args[1].data["cursor_id"] = context["cursor_id"]
            try:
                result = f(*args, **kwargs)
                if fetch_all:
                    cursor = actions.load_cursor_from_context(context)
                    session = actions.load_session_from_context(context)
                    if not result:
                        result = {}
                    # Initial server-side cursors do not contain any description before
                    # the first row is fetched. Therefore, we have to try to fetch the
                    # first one - if successful, we a description if not,
                    # nothing is returned.
                    # But: After the last row the cursor will 'forget' its description.
                    # Therefore we have to fetch the remaining data later.

                    # Set of triggers after all the data was fetched.
                    # The cursor must not be closed earlier!
                    triggers = [
                        actions.close_cursor,
                        actions.close_raw_connection,
                        session.connection.commit,
                    ]
                    trigger_args = [({}, context), ({}, context), tuple()]
                    first = None
                    if not named or cursor.statusmessage:
                        try:
                            first = cursor.fetchone()
                        except psycopg2.ProgrammingError as e:
                            if not e.args or e.args[0] != "no results to fetch":
                                raise e
                        except psycopg2.errors.InvalidCursorName as e:
                            print(e)
                    if first:
                        first = map(actions._translate_fetched_cell, first)
                        if cursor.description:
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
                            result["data"] = (
                                x
                                for x in itertools.chain(
                                    [first],
                                    transform_results(cursor, triggers, trigger_args),
                                )
                            )
                            result["description"] = description
                            result["context"] = context
                            result["rowcount"] = cursor.rowcount
                            triggered_close = True
                    if not triggered_close and artificial_connection:
                        session.connection.commit()
            finally:
                if not triggered_close:
                    if fetch_all and not artificial_connection:
                        actions.close_cursor({}, context)
                    if artificial_connection:
                        actions.close_raw_connection({}, context)
            return result

        return wrapper

    return inner


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
        table = kwargs.get("table") or kwargs.get("sequence")
        actions.assert_permission(request.user, table, permission)
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
        if schema not in EDITABLE_SCHEMAS:
            raise PermissionDenied
        if schema.startswith("_"):
            raise PermissionDenied
        if request.user.is_anonymous:
            raise PermissionDenied
        if actions.has_sequence(dict(schema=schema, sequence_name=sequence), {}):
            raise APIError("Sequence already exists")
        return self.__create_sequence(request, schema, sequence, request.data)

    @api_exception
    @require_delete_permission
    def delete(self, request, schema, sequence):
        if schema not in EDITABLE_SCHEMAS:
            raise PermissionDenied
        if schema.startswith("_"):
            raise PermissionDenied
        if request.user.is_anonymous:
            raise PermissionDenied
        return self.__delete_sequence(request, schema, sequence, request.data)

    @load_cursor()
    def __delete_sequence(self, request, schema, sequence, jsn):
        seq = sqla.schema.Sequence(sequence, schema=schema)
        seq.drop(bind=actions._get_engine())
        return JsonResponse({}, status=status.HTTP_200_OK)

    @load_cursor()
    def __create_sequence(self, request, schema, sequence, jsn):
        seq = sqla.schema.Sequence(sequence, schema=schema)
        seq.create(bind=actions._get_engine())
        return JsonResponse({}, status=status.HTTP_201_CREATED)


class Metadata(APIView):
    @api_exception
    def get(self, request, table, schema=None):
        """schema will be ignored"""
        table_obj = actions.get_django_table_obj(table)
        metadata = table_obj.oemetadata
        return JsonResponse(metadata)

    @api_exception
    @require_write_permission
    @load_cursor()
    def post(self, request, table, schema=None):
        """schema will be ignored"""
        table_obj = actions.get_django_table_obj(table)
        schema = table_obj.schema.name

        raw_input = request.data
        metadata, error = actions.try_parse_metadata(raw_input)

        if metadata is not None:
            cursor = actions.load_cursor_from_context(request.data)

            # update/sync keywords with tags before saving metadata
            keywords = metadata.keywords or []

            # get_tag_keywords_synchronized_metadata returns the OLD metadata
            # but with the now harmonized keywords (harmonized with tags)
            # so we only copy the resulting keywords before storing the metadata
            _metadata = get_tag_keywords_synchronized_metadata(
                table=table, schema=schema, keywords_new=keywords
            )
            metadata.keywords = _metadata["keywords"]

            # Write oemetadata json to dataedit.models.tables oemetadata(JSONB) field
            # and to SQL comment on table
            actions.set_table_metadata(
                table=table, schema=schema, metadata=metadata, cursor=cursor
            )
            _metadata = get_tag_keywords_synchronized_metadata(
                table=table, schema=schema, keywords_new=keywords
            )
            metadata.keywords = _metadata["keywords"]

            actions.set_table_metadata(
                table=table, schema=schema, metadata=metadata, cursor=cursor
            )
            return JsonResponse(raw_input)
        else:
            raise APIError(error)


class Table(APIView):
    """
    Handels the creation of tables and serves information on existing tables
    """

    @api_exception
    def get(self, request, table, schema=None):
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
        # schema will be ignored
        table_obj = actions.get_django_table_obj(table)
        schema = table_obj.schema.name

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
    def post(self, request, table, schema=None):
        """
        Changes properties of tables and table columns
        :param request:
        :param schema:
        :param table:
        :return:
        """
        # schema will be ignored
        table_obj = actions.get_django_table_obj(table, only_editable=True)
        schema = table_obj.schema.name

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
    def put(self, request, table, schema=None):
        """
        Every request to unsave http methods have to contain a "csrftoken".
        This token is used to deny cross site reference forwarding.
        In every request the header had to contain "X-CSRFToken"
        with the actual csrftoken.
        The token can be requested at / and will be returned as cookie.

        :param request:
        :return:
        """
        schema = schema or DEFAULT_SCHEMA
        if schema not in EDITABLE_SCHEMAS:
            raise PermissionDenied
        if request.user.is_anonymous:
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
        metadata = json_data.get("metadata")

        self.__create_table(
            request,
            schema,
            table,
            column_definitions,
            constraint_definitions,
            metadata=metadata,
        )

        perm, _ = login_models.UserPermission.objects.get_or_create(
            table=actions.get_django_table_obj(table), holder=request.user
        )
        perm.level = login_models.ADMIN_PERM
        perm.save()
        request.user.save()
        return JsonResponse({}, status=status.HTTP_201_CREATED)

    def validate_column_names(self, column_definitions):
        """Raise APIError if any column name is invalid"""

        for c in column_definitions:
            colname = c["name"]

            err_msg = (
                f"Unsupported column name: '{colname}'\n"
                "Column name must consist of lowercase alpha-numeric "
                f"words or underscores and start with a letter. "
                "It must not start with an underscore or exceed "
                f"{MAX_COL_NAME_LENGTH} characters "
                f"(current column name length: {len(colname)})."
            )
            if not colname.isidentifier():
                raise APIError(f"{err_msg}")
            if re.search(r"[A-Z]", colname) or re.match(r"_", colname):
                raise APIError(
                    "Column names must not contain capital letters "
                    f"or start with an underscore! {err_msg}"
                )
            if len(colname) > MAX_COL_NAME_LENGTH:
                raise APIError(f"Column name is too long! {err_msg}")

    @load_cursor()
    def __create_table(
        self,
        request,
        schema,
        table,
        column_definitions,
        constraint_definitions,
        metadata=None,
    ):
        self.validate_column_names(column_definitions)
        try:
            table_object = DBTable.create_with_schema(table, schema_name=schema)
        except IntegrityError:
            raise APIError("Table aready exists")

        context = {
            "connection_id": actions.get_or_403(request.data, "connection_id"),
            "cursor_id": actions.get_or_403(request.data, "cursor_id"),
        }
        cursor = sessions.load_cursor_from_context(context)
        actions.table_create(
            schema,
            table,
            column_definitions,
            constraint_definitions,
        )
        table_object.save()

        if metadata:
            actions.set_table_metadata(
                table=table, schema=schema, metadata=metadata, cursor=cursor
            )

    @api_exception
    @require_delete_permission
    def delete(self, request, table, schema=None):
        # schema will be ignored
        table_obj = actions.get_django_table_obj(table, only_editable=True)
        schema = table_obj.schema.name

        meta_schema = actions.get_meta_schema_name(schema)

        edit_table = actions.get_edit_table_name(schema, table)
        actions._get_engine().execute(
            'DROP TABLE "{schema}"."{table}" CASCADE;'.format(
                schema=meta_schema, table=edit_table
            )
        )

        edit_table = actions.get_insert_table_name(schema, table)
        actions._get_engine().execute(
            'DROP TABLE "{schema}"."{table}" CASCADE;'.format(
                schema=meta_schema, table=edit_table
            )
        )

        edit_table = actions.get_delete_table_name(schema, table)
        actions._get_engine().execute(
            'DROP TABLE "{schema}"."{table}" CASCADE;'.format(
                schema=meta_schema, table=edit_table
            )
        )

        actions._get_engine().execute(
            'DROP TABLE "{schema}"."{table}" CASCADE;'.format(
                schema=schema, table=table
            )
        )
        table_object = DBTable.objects.get(name=table)
        table_object.delete()
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
        schema, table = actions.get_schema_and_table_name(table, restrict_schemas=False)
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
        schema, table = actions.get_schema_and_table_name(table)
        response = actions.column_alter(
            request.data["query"], {}, schema, table, column
        )
        return JsonResponse(response)

    @api_exception
    @require_write_permission
    def put(self, request, schema, table, column):
        schema, table = actions.get_schema_and_table_name(table)
        actions.column_add(schema, table, column, request.data["query"])
        return JsonResponse({}, status=201)


class Fields(APIView):
    def get(self, request, schema, table, id, column=None):
        schema, table = actions.get_schema_and_table_name(table, restrict_schemas=False)
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


class Move(APIView):
    @require_admin_permission
    @api_exception
    def post(self, request, table: str, topic: str, schema: str = None):
        """With the removal of schemas,  we physicall will only move tables between
        DRAFT_SCHEMA and DATASET_SCHEMA (draft and published).
        However, if the target schema isa topic, we will attach that information

        In consequence, this is equivalent to publish/unpublish
        """

        # schema will be ignored
        table_obj = actions.get_django_table_obj(table)
        schema = table_obj.schema.name

        if topic == DRAFT_SCHEMA and table_obj.is_published:
            # unpublish: move back into draft
            target_schema = DRAFT_SCHEMA
        elif table_obj.is_draft:
            # publish
            target_schema = DATASET_SCHEMA
        else:
            raise APIError(
                f"exactly one of origin and target schema must be {DRAFT_SCHEMA}, "
                f"got {schema}, {topic}"
            )

        actions.move(schema, table, target_schema)

        # add topic, if it exists
        topic_objs = Topic.objects.filter(name=topic)
        if topic_objs.exists():
            # according to doc, usind `add` does not create duplicates
            table_obj.topics.add(topic_objs.first())

        return HttpResponse(status=status.HTTP_200_OK)


class Rows(APIView):
    @api_exception
    def get(self, request, table, row_id=None, schema=None):
        table_obj = actions.get_django_table_obj(table)
        schema = table_obj.schema.name

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
        # If you connect two values with an +, it will convert the + to a space.
        # Whatever.

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
        session = (
            sessions.load_session_from_context(return_obj.pop("context"))
            if "context" in return_obj
            else None
        )
        # Extract column names from description
        if "description" in return_obj:
            cols = [col[0] for col in return_obj["description"]]
        else:
            cols = []
            return_obj["data"] = []
            return_obj["rowcount"] = 0
        if format == "csv":
            pseudo_buffer = Echo()

            # NOTE: the csv downloader for views (client side)
            # in dataedit/static/dataedit/backend.js: parse_download()
            # uses JSON.stringify, so we use csv.QUOTE_NONNUMERIC
            # to get somewhat consistent results

            writer = csv.writer(pseudo_buffer, quoting=csv.QUOTE_NONNUMERIC)
            response = OEPStream(
                (
                    writer.writerow(x)
                    for x in itertools.chain([cols], return_obj["data"])
                ),
                content_type="text/csv",
                session=session,
            )
            response[
                "Content-Disposition"
            ] = 'attachment; filename="{schema}__{table}.csv"'.format(
                schema=schema, table=table
            )
            return response
        elif format == "datapackage":
            pseudo_buffer = Echo()
            writer = csv.writer(pseudo_buffer, quoting=csv.QUOTE_ALL)
            zf = zipstream.ZipFile(mode="w", compression=zipstream.ZIP_DEFLATED)
            csv_name = "{schema}__{table}.csv".format(schema=schema, table=table)
            zf.write_iter(
                csv_name,
                (
                    writer.writerow(x).encode("utf-8")
                    for x in itertools.chain([cols], return_obj["data"])
                ),
            )
            table_obj = actions._get_table(schema=schema, table=table)
            if table_obj.comment:
                zf.writestr("datapackage.json", table_obj.comment.encode("utf-8"))
            else:
                zf.writestr(
                    "datapackage.json",
                    json.dumps(JSONCompiler().visit(OEPMetadata())).encode("utf-8"),
                )
            response = OEPStream(
                (chunk for chunk in zf),
                content_type="application/zip",
                session=session,
            )
            response[
                "Content-Disposition"
            ] = 'attachment; filename="{schema}__{table}.zip"'.format(
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

            return stream(
                (dict(zip(cols, row)) for row in return_obj["data"]), session=session
            )

    @api_exception
    @require_write_permission
    def post(self, request, schema, table, row_id=None, action=None):
        schema, table = actions.get_schema_and_table_name(table)
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
        schema, table = actions.get_schema_and_table_name(table)
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
        schema, table = actions.get_schema_and_table_name(table)
        result = self.__delete_rows(request, schema, table, row_id)
        actions.apply_changes(schema, table)
        return JsonResponse(result)

    @load_cursor()
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
                    row_id,
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

    @load_cursor()
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

    @load_cursor()
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
                    row_id,
                    {"type": "column", "column": "id"},
                ],
                "type": "operator",
            }
            where = query.get("where")
            if where:
                clause = conjunction([clause, where])
            query["where"] = clause

        return actions.data_update(query, context)

    @load_cursor(named=True)
    def __get_rows(self, request, data):
        table = actions._get_table(data["schema"], table=data["table"])
        # params = {}
        # params_count = 0
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


class Session(APIView):
    def get(self, request, length=1):
        return request.session["resonse"]


def date_handler(obj):
    """
    Implements a handler to serialize dates in JSON-strings
    :param obj: An object
    :return: The str method is called (which is the default serializer for JSON)
        unless the object has an attribute  *isoformat*
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
    :return: A JSON-Response that contains a dictionary with
      the corresponding response stored in *content*
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
            session = (
                sessions.load_session_from_context(result.pop("context"))
                if "context" in result
                else None
            )
            return stream(
                result,
                allow_cors=allow_cors and request.user.is_anonymous,
                session=session,
            )

        def execute(self, request):
            if requires_cursor:
                return load_cursor()(self._internal_execute)(self, request)
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
            except Exception:
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
        return OEPStream(
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


def stream(data, allow_cors=False, status_code=status.HTTP_200_OK, session=None):
    encoder = GeneratorJSONEncoder()
    response = OEPStream(
        encoder.iterencode(data),
        content_type="application/json",
        status=status_code,
        session=session,
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


def oeo_search(request):
    # get query from user request # TODO validate input to prevent sneaky stuff
    query = request.GET["query"]
    # call local search service
    # TODO: this url should not be hardcoded here - get it from oeplatform/settings.py
    url = f"http://loep/lookup-application/api/search?query={query}"
    res = requests.get(url).json()
    # res: something like [{"label": "testlabel", "resource": "testresource"}]
    # send back to client
    return JsonResponse(res, safe=False)
