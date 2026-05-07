__license__ = """
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Eike Broda <https://github.com/ebroda>
SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>  © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Christian Hofmann <https://github.com/christian-rli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 chrwm <https://github.com/chrwm> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 user <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import itertools
import json
import logging
import re
from decimal import Decimal
from typing import Callable, Union

import geoalchemy2  # noqa:F401 Although this import seems unused is has to be here
import psycopg2
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest, JsonResponse, StreamingHttpResponse
from django.http.response import Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

import login.permissions
from api import parser, sessions
from api.actions import (
    assert_permission,
    close_cursor,
    close_raw_connection,
    describe_columns,
    describe_constraints,
    load_cursor_from_context,
    load_session_from_context,
    open_cursor,
    open_raw_connection,
    translate_fetched_cell,
)
from api.encode import GeneratorJSONEncoder
from api.error import APIError
from api.utils import table_or_404_from_dict
from dataedit.models import Embargo, Table, Tag

logger = logging.getLogger("oeplatform")

# Response is from rest framework, OEPStream has content_type json
JsonLikeResponse = Union[JsonResponse, Response, "OEPStream", "ModJsonResponse"]


WHERE_EXPRESSION = re.compile(
    r"^(?P<first>[\w\d_\.]+)\s*(?P<operator>"
    + r"|".join(parser.sql_operators)
    + r")\s*(?P<second>(?![>=]).+)$"
)


class ModJsonResponse(JsonResponse):
    def __init__(self, dictionary: dict):
        if dictionary["success"]:
            super().__init__({}, status=200)
        elif dictionary["error"] is not None:
            super().__init__(
                {}, status=dictionary["http_status"], reason=dictionary["error"]
            )
        else:
            super().__init__({}, status=dictionary["http_status"])


def transform_results(cursor, triggers, trigger_args):
    row = cursor.fetchone() if not cursor.closed else None
    while row is not None:
        yield list(map(translate_fetched_cell, row))
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
    def inner(f: Callable):
        def wrapper(*args, **kwargs) -> dict:
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
                    context.update(open_raw_connection({}, context))
                    args[1].data["connection_id"] = context["connection_id"]
                if "cursor_id" in args[1].data:
                    context["cursor_id"] = args[1].data["cursor_id"]
                else:
                    context.update(open_cursor({}, context, named=named))
                    args[1].data["cursor_id"] = context["cursor_id"]
            try:
                result = f(*args, **kwargs)
                if fetch_all:
                    cursor = load_cursor_from_context(context)
                    session = load_session_from_context(context)
                    connection = session.connection

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
                        close_cursor,
                        close_raw_connection,
                        connection.commit,
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
                            logger.error(str(e))
                    if first:
                        first = map(translate_fetched_cell, first)
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
                        connection.commit()
            finally:
                if not triggered_close:
                    if fetch_all and not artificial_connection:
                        close_cursor({}, context)
                    if artificial_connection:
                        close_raw_connection({}, context)
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


def api_exception(
    f: Callable[..., JsonLikeResponse],
) -> Callable[..., JsonLikeResponse]:
    """Catch all internal errors and ensure than we return JSON-like response

    if we catch an APIError, we return the error message to the user, otherwise
    a generic error message

    """

    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            return JsonResponse({"reason": e.message}, status=e.status)
        except (Table.DoesNotExist, Http404):
            return JsonResponse({"reason": "table does not exist"}, status=404)
        except Exception as exc:
            # All other Errors: dont accidently return sensitive data from error
            # but return generic error message
            logger.error(str(exc))
            return JsonResponse({"reason": "Invalid request"}, status=400)

    return wrapper


def permission_wrapper(permission: int, f: Callable) -> Callable:
    def wrapper(caller, request: HttpRequest, *args, **kwargs):
        table_obj = table_or_404_from_dict(kwargs)
        assert_permission(user=request.user, table=table_obj, permission=permission)
        return f(caller, request, *args, **kwargs)

    return wrapper


def require_write_permission(f: Callable) -> Callable:
    return permission_wrapper(login.permissions.WRITE_PERM, f)


def require_delete_permission(f: Callable) -> Callable:
    return permission_wrapper(login.permissions.DELETE_PERM, f)


def require_admin_permission(f: Callable) -> Callable:
    return permission_wrapper(login.permissions.ADMIN_PERM, f)


def conjunction(clauses) -> dict:
    return {"type": "operator", "operator": "AND", "operands": clauses}


def check_embargo(table_obj: Table) -> bool:
    try:
        embargo = Embargo.objects.filter(table=table_obj).first()
        if embargo and embargo.date_ended and embargo.date_ended > timezone.now():
            return True
        return False
    except ObjectDoesNotExist:
        return False


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
        def options(self, request: HttpRequest, *args, **kwargs) -> JsonLikeResponse:
            return JsonResponse({})

        @cors(allow_cors)
        @api_exception
        def post(self, request: HttpRequest) -> JsonLikeResponse:
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

        def execute(self, request: HttpRequest):
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


def stream(
    data, allow_cors=False, status_code=status.HTTP_200_OK, session=None
) -> OEPStream:
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


def update_tags_from_keywords(table: str, keywords: list[str]) -> list[str]:
    table_obj = Table.objects.get(name=table)
    table_obj.tags.clear()
    keywords_new = set()
    for keyword in keywords:
        tag = Tag.get_or_create_from_name(keyword)
        table_obj.tags.add(tag)
        keywords_new.add(tag.name_normalized)
    table_obj.save()
    return list(keywords_new)


def get_request_data_dict(request: Request) -> dict:
    if isinstance(request.data, dict):
        return request.data
    raise TypeError(type(request.data))


def get_column_description(table_obj: Table):
    """Return list of column descriptions:
    [{
       "name": str,
       "data_type": str,
       "is_nullable": bool,
       "is_pk": bool
    }]

    """

    def get_datatype_str(column_def):
        """get single string sql type definition.

        We want the data type definition to be a simple string, e.g. decimal(10, 6)
        or varchar(128), so we need to combine the various fields
        (type, numeric_precision, numeric_scale, ...)
        """
        # for reverse validation, see also api.parser.parse_type(dt_string)
        dt = column_def["data_type"].lower()
        precisions = None
        if dt.startswith("character"):
            if dt == "character varying":
                dt = "varchar"
            else:
                dt = "char"
            precisions = [column_def["character_maximum_length"]]
        elif dt.endswith(" without time zone"):  # this is the default
            dt = dt.replace(" without time zone", "")
        elif re.match("(numeric|decimal)", dt):
            precisions = [column_def["numeric_precision"], column_def["numeric_scale"]]
        elif dt == "interval":
            precisions = [column_def["interval_precision"]]
        elif re.match(".*int", dt) and re.match(
            "nextval", column_def.get("column_default") or ""
        ):
            # dt = dt.replace('int', 'serial')
            pass
        elif dt.startswith("double"):
            dt = "float"
        if precisions:  # remove None
            precisions = [x for x in precisions if x is not None]
        if precisions:
            dt += "(%s)" % ", ".join(str(x) for x in precisions)
        return dt

    def get_pk_fields(constraints):
        """Get the column names that make up the primary key
        from the constraints definitions.

        NOTE: Currently, the wizard to create tables only supports
            single fields primary keys (which is advisable anyways)
        """
        pk_fields = []
        for _name, constraint in constraints.items():
            if constraint.get("constraint_type") == "PRIMARY KEY":
                m = re.match(
                    r"PRIMARY KEY[ ]*\(([^)]+)", constraint.get("definition") or ""
                )
                if m:
                    # "f1, f2" -> ["f1", "f2"]
                    pk_fields = [x.strip() for x in m.groups()[0].split(",")]
        return pk_fields

    _columns = describe_columns(table_obj)
    _constraints = describe_constraints(table_obj)
    pk_fields = get_pk_fields(_constraints)
    # order by ordinal_position
    columns = []
    for name, col in sorted(
        _columns.items(), key=lambda kv: int(kv[1]["ordinal_position"])
    ):
        columns.append(
            {
                "name": name,
                "data_type": get_datatype_str(col),
                "is_nullable": col["is_nullable"],
                "is_pk": name in pk_fields,
                "unit": None,
                "description": None,
            }
        )
    return columns


def sync_api_metadata_columns(metadata: dict, table_obj: Table) -> dict:
    """
    Enforces that the metadata 'fields' exactly match the physical database columns,
    while preserving human annotations (isAbout, valueReference, etc.).
    """
    # 1. Get the physical truths from the database
    physical_columns = get_column_description(table_obj)

    # Ensure resources array exists safely
    if not metadata.get("resources"):
        metadata["resources"] = [{}]
    resource = metadata["resources"][0]

    if "schema" not in resource:
        resource["schema"] = {}

    # 2. Extract incoming fields from the API payload
    incoming_fields = resource["schema"].get("fields", [])

    # Create a fast lookup dict by column name
    incoming_fields_lookup = {
        field.get("name"): field
        for field in incoming_fields
        if isinstance(field, dict) and field.get("name")
    }

    updated_fields = []

    # 3. Iterate through physical database columns (The Source of Truth)
    for db_col in physical_columns:
        col_name = db_col["name"]

        # Grab the incoming human data if it exists, otherwise empty dict
        incoming_col = incoming_fields_lookup.get(col_name, {})

        # Ensure 'id' is strictly not nullable
        is_nullable = db_col["is_nullable"]
        if col_name == "id":
            is_nullable = False

        # Start with a copy of the incoming column to preserve all human annotations
        # (isAbout, valueReference, description, unit, etc.)
        merged_col = incoming_col.copy()

        # Overwrite physical constraints strictly based on the database
        merged_col.update(
            {
                "name": col_name,
                "type": db_col["data_type"],
                "nullable": is_nullable,
            }
        )

        # Ensure default keys exist if they weren't in the incoming payload
        merged_col.setdefault("description", None)
        merged_col.setdefault("unit", None)

        # --- ARTIFACT SCRUBBER ---
        # Just in case a user copy-pasted raw JSON from the UI into an API tool,
        # we scrub the UI-only 'openModalButton' to keep the DB clean.
        if isinstance(merged_col.get("isAbout"), list):
            for item in merged_col["isAbout"]:
                item.pop("openModalButton", None)

        if isinstance(merged_col.get("valueReference"), list):
            for item in merged_col["valueReference"]:
                item.pop("openModalButton", None)

        updated_fields.append(merged_col)

    # 4. Overwrite the payload's fields with our perfectly reconciled list
    # Note: Because we iterate over `physical_columns`, any "phantom" columns
    # that were in the JSON but not in the DB are automatically dropped!
    resource["schema"]["fields"] = updated_fields

    return metadata
