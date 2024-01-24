import itertools

import psycopg2

from api import actions
from api.utilities import transform_results


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