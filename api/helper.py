"""
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

import geoalchemy2  # noqa: Although this import seems unused is has to be here
import psycopg2
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest, JsonResponse, StreamingHttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

import login.permissions
from api import parser, sessions
from api.actions import (
    _translate_fetched_cell,
    assert_permission,
    close_cursor,
    close_raw_connection,
    load_cursor_from_context,
    load_session_from_context,
    open_cursor,
    open_raw_connection,
)
from api.encode import GeneratorJSONEncoder
from api.error import APIError
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
        yield list(map(_translate_fetched_cell, row))
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
                        first = map(_translate_fetched_cell, first)
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
        except Table.DoesNotExist:
            return JsonResponse({"reason": "table does not exist"}, status=404)

        # TODO: why cant' we handle all other errors here? (tests failing)
        # except Exception as exc:
        #    # All other Errors: dont accidently return sensitive data from error
        #    # but return generic error message
        #    logger.error(str(exc))
        #    return JsonResponse({"reason": "Invalid request."}, status=400)

    return wrapper


def permission_wrapper(permission: int, f: Callable) -> Callable:
    def wrapper(caller, request: HttpRequest, *args, **kwargs):
        table = kwargs.get("table") or kwargs.get("sequence") or ""
        assert_permission(user=request.user, table=table, permission=permission)
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


def check_embargo(schema: str, table: str) -> bool:
    try:
        table_obj = Table.objects.get(name=table)
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
