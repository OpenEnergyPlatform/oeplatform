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

import csv
import itertools
import json
import re
from datetime import datetime, timedelta

import geoalchemy2  # noqa: Although this import seems unused is has to be here
import requests
import zipstream
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.search import TrigramSimilarity
from django.db import DatabaseError, transaction
from django.db.models import Q
from django.db.utils import IntegrityError
from django.http import Http404, HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from oemetadata.latest.template import OEMETADATA_LATEST_TEMPLATE
from rest_framework import generics, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

import api.parser
import login.models as login_models
from api import actions, parser, sessions
from api.actions import table_get_approx_row_count
from api.encode import Echo
from api.error import APIError
from api.helper import (
    WHERE_EXPRESSION,
    JsonLikeResponse,
    ModJsonResponse,
    OEPStream,
    api_exception,
    check_embargo,
    conjunction,
    create_ajax_handler,
    date_handler,
    get_request_data_dict,
    load_cursor,
    require_admin_permission,
    require_delete_permission,
    require_write_permission,
    stream,
    update_tags_from_keywords,
)
from api.parser import query_typecast_select
from api.serializers import (
    EnergyframeworkSerializer,
    EnergymodelSerializer,
    ScenarioBundleScenarioDatasetSerializer,
    ScenarioDataTablesSerializer,
)
from api.services.embargo import (
    EmbargoValidationError,
    apply_embargo,
    parse_embargo_payload,
)
from api.services.permissions import assign_table_holder
from api.services.table_creation import TableCreationOrchestrator
from api.utils import get_dataset_configs, validate_schema
from api.validators.column import MAX_COL_NAME_LENGTH, validate_column_names
from api.validators.identifier import assert_valid_identifier_name
from dataedit.models import Embargo, Table
from factsheet.permission_decorator import post_only_if_user_is_owner_of_scenario_bundle
from modelview.models import Energyframework, Energymodel
from oedb.connection import _get_engine
from oekg.utils import (
    execute_sparql_query,
    process_datasets_sparql_query,
    validate_public_sparql_query,
)
from oeplatform.settings import (
    DBPEDIA_LOOKUP_SPARQL_ENDPOINT_URL,
    ONTOP_SPARQL_ENDPOINT_URL,
    USE_LOEP,
    USE_ONTOP,
)

# when running approximate (fast) row count: if number is below this
# we get the precise row count (slow)
APPROX_ROW_COUNT_DEFAULT_PRECISE_BELOW = 0


class SequenceAPIView(APIView):
    @api_exception
    def put(self, request: Request, schema: str, sequence: str) -> JsonLikeResponse:
        schema = validate_schema(schema)
        if schema.startswith("_"):
            raise APIError("Schema starts with _, which is not allowed")
        if request.user.is_anonymous:
            raise APIError("User is anonymous", 401)
        if actions.has_table(dict(schema=schema, sequence_name=sequence), {}):
            raise APIError("Sequence already exists", 409)
        return JsonResponse(self.__create_sequence(request, schema, sequence))

    @api_exception
    @require_delete_permission
    def delete(self, request: Request, schema: str, sequence: str) -> JsonLikeResponse:
        schema = validate_schema(schema)
        if schema.startswith("_"):
            raise APIError("Schema starts with _, which is not allowed")
        if request.user.is_anonymous:
            raise APIError("User is anonymous", 401)
        return JsonResponse(self.__delete_sequence(request, schema, sequence))

    @load_cursor()
    def __delete_sequence(
        self, request: Request, schema: str, sequence: str
    ) -> JsonLikeResponse:
        actions.delete_sequence(sequence=sequence, schema=schema)
        return JsonResponse({}, status=status.HTTP_200_OK)

    @load_cursor()
    def __create_sequence(
        self, request: Request, schema: str, sequence: str
    ) -> JsonLikeResponse:
        actions.create_sequence(sequence=sequence, schema=schema)
        return JsonResponse({}, status=status.HTTP_201_CREATED)


class MetadataAPIView(APIView):
    @api_exception
    @method_decorator(never_cache)
    def get(self, request: Request, schema: str, table: str) -> JsonLikeResponse:
        metadata = actions.get_table_metadata(schema, table)
        return JsonResponse(metadata)

    @api_exception
    @require_write_permission
    @load_cursor()
    def post(self, request: Request, schema: str, table: str) -> JsonLikeResponse:
        raw_input = request.data
        metadata, error = actions.try_parse_metadata(raw_input)

        if not error and metadata is not None:
            metadata = actions.try_convert_metadata_to_v2(metadata)

        if not error:
            metadata, error = actions.try_validate_metadata(metadata)

        if metadata is not None:

            # update/sync keywords with tags before saving metadata
            # TODO make this iter over all resources
            keywords = metadata["resources"][0].get("keywords", []) or []
            metadata["resources"][0]["keywords"] = update_tags_from_keywords(
                table=table, keywords=keywords
            )

            # make sure extra metadata is removed
            metadata.pop("connection_id", None)
            metadata.pop("cursor_id", None)

            actions.set_table_metadata(table=table, metadata=metadata)
            return JsonResponse(raw_input)
        else:
            raise APIError(error)


class TableAPIView(APIView):
    """
    Handles the creation of tables and serves information on existing tables
    """

    objects = None

    @api_exception
    @method_decorator(never_cache)
    def get(self, request: Request, schema: str, table: str) -> JsonLikeResponse:
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
    def post(self, request: Request, schema: str, table: str) -> JsonLikeResponse:
        """
        Changes properties of tables and table columns
        :param request:
        :param schema:
        :param table:
        :return:
        """
        schema = validate_schema(schema)
        if schema.startswith("_"):
            raise APIError("Schema starts with _, which is not allowed")
        request_data_dict = get_request_data_dict(request)

        if "column" in request_data_dict["type"]:
            column_definition = api.parser.parse_scolumnd_from_columnd(
                schema, table, request_data_dict["name"], request_data_dict
            )
            result = actions.queue_column_change(schema, table, column_definition)
            return ModJsonResponse(result)

        elif "constraint" in request_data_dict["type"]:
            # Input has nothing to do with DDL from Postgres.
            # Input is completely different.
            # dict.get() returns None, if key does not exist
            constraint_definition = {
                "action": request_data_dict["action"],  # {ADD, DROP}
                "constraint_type": request_data_dict.get(
                    "constraint_type"
                ),  # {FOREIGN KEY, PRIMARY KEY, UNIQUE, CHECK}
                "constraint_name": request_data_dict.get(
                    "constraint_name"
                ),  # {myForeignKey, myUniqueConstraint}
                "constraint_parameter": request_data_dict.get("constraint_parameter"),
                # Things in Brackets, e.g. name of column
                "reference_table": request_data_dict.get("reference_table"),
                "reference_column": request_data_dict.get("reference_column"),
            }

            result = actions.queue_constraint_change(
                schema, table, constraint_definition
            )
            return ModJsonResponse(result)
        else:
            return ModJsonResponse(
                actions.get_response_dict(False, 400, "type not recognised")
            )

    @api_exception
    def put(self, request: Request, schema: str, table: str) -> JsonLikeResponse:
        """
        Creates a new table: physical table first, then metadata row.
        Applies embargo and permissions, and sets metadata if provided.

        REST-API endpoint used to create a new table in the database.
        The table is created with the columns and constraints specified in the
        request body. The request body must contain a JSON object with the following
        keys: 'columns', 'constraints' and 'metadata'.
        The payload must be a  groped in a 'query' key.

        For authentication, the request must contain a valid token in the
        Authentication header.

        Args:
            request: The request object
            schema: The schema in which the table should be created
            table: The name of the table to be created

        Returns:
            JsonResponse: A JSON response with the status code 201 CREATED

        """
        schema = validate_schema(schema)
        # 1) Basic schema checks
        if schema.startswith("_"):
            raise APIError("Schema starts with _, which is not allowed")
        if request.user.is_anonymous:
            raise APIError("User is anonymous", 401)
        if actions.has_table({"schema": schema, "table": table}, {}):
            raise APIError("Table already exists", 409)

        # 2) Validate identifiers
        assert_valid_identifier_name(table)

        # 3) Parse and validate payload
        request_data_dict = get_request_data_dict(request)
        payload_query = request_data_dict.get("query", {})
        columns = payload_query.get("columns")
        if not columns:
            raise APIError("Table contains no columns")
        for col in columns:
            col.update({"c_schema": schema, "c_table": table})
        validate_column_names(columns)

        constraints = payload_query.get("constraints", [])
        for cons in constraints:
            cons.update({"action": "ADD", "c_schema": schema, "c_table": table})

        embargo_data = request_data_dict.get("embargo") or payload_query.get(
            "embargo", {}
        )
        try:
            embargo_required = parse_embargo_payload(embargo_data)
        except EmbargoValidationError as e:
            raise APIError(str(e))

        # 4) Create the table (physical → metadata) atomically
        orchestrator = TableCreationOrchestrator()
        table_obj = orchestrator.create_table(
            schema=schema,
            table=table,
            column_defs=columns,
            constraint_defs=constraints,
        )

        # 5) Post-creation hooks
        if embargo_required:
            apply_embargo(table_obj, embargo_data)

        assign_table_holder(request.user, schema, table)

        metadata = payload_query.get("metadata")
        if metadata:

            actions.set_table_metadata(table=table, metadata=metadata)

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

    def oep_create_table_transaction(
        self,
        schema: str,
        table: str,
        column_definitions,
        constraint_definitions,
    ):
        """
        This method handles atomic table creation transactions on the OEP. It
        attempts to create first the django table objects and stored it in
        dataedit_tables table. Then it attempts to create the OEDB table.
        If there is an error raised during the first two steps the function
        will cleanup any table object or table artifacts created during the
        process. The order of execution matters, it should always first
        create the django table object.

        Params:
            django_schema_object: The schema object stored in the django
                database
            schema:
            table
            column_definitions
            constraint_definitions

        returns:
            table_object: The django table objects that was created
        """

        try:
            with transaction.atomic():
                # First create the table object in the django database.
                table_object = self._create_table_object(table=table)
            # Then attempt to create the OEDB table to check
            # if creation will succeed - action includes checks
            # and will raise api errors
            actions.table_create(
                schema, table, column_definitions, constraint_definitions
            )
        except DatabaseError as e:
            # remove any oedb table artifacts left after table creation
            # transaction failed
            self.__remove_oedb_table_on_exception_raised_during_creation_transaction(
                table, schema
            )

            # also remove any django table object
            # find the created django table object
            object_to_delete = Table.objects.filter(name=table)
            # delete it if it exists
            if object_to_delete.exists():
                object_to_delete.delete()

            raise APIError(
                message="Error during table creation transaction. All table fragments"
                f"have been removed. For further details see: {e}"
            )

        # for now only return the django table object
        # TODO: Check if is necessary to return the response dict returned by the oedb
        # table creation function
        return table_object

    def __remove_oedb_table_on_exception_raised_during_creation_transaction(
        self, table: str, schema: str
    ):
        """
        This private method handles removing a table form the OEDB only for the case
        where an error was raised during table creation. It specifically will delete
        the OEDB table created by the user and also the edit_ meta(revision) table
        that is automatically created in the background.
        """

        # find the created oedb table
        if actions.has_table({"table": table, "schema": schema}):
            # get table and schema names, also for meta(revision) tables
            schema, table = actions.get_table_name(schema, table)
            meta_schema = actions.get_meta_schema_name(schema)

            # drop the revision table with edit_ prefix
            edit_table = actions.get_edit_table_name(schema, table)
            _get_engine().execute(
                'DROP TABLE "{schema}"."{table}" CASCADE;'.format(
                    schema=meta_schema, table=edit_table
                )
            )
            # drop the data table
            _get_engine().execute(
                'DROP TABLE "{schema}"."{table}" CASCADE;'.format(
                    schema=schema, table=table
                )
            )

    @load_cursor()
    def __create_table(
        self,
        request: Request,
        schema: str,
        table: str,
        column_definitions,
        constraint_definitions,
        metadata=None,
        embargo_data=None,
    ):
        assert_valid_identifier_name(table)
        self.validate_column_names(column_definitions)

        embargo_error, embargo_payload_check = self._check_embargo_payload_valid(
            embargo_data
        )
        if embargo_error:
            raise embargo_error

        if embargo_payload_check:
            table_object = self.oep_create_table_transaction(
                table=table,
                schema=schema,
                column_definitions=column_definitions,
                constraint_definitions=constraint_definitions,
            )
            self._apply_embargo(table_object, embargo_data)

            if metadata:
                actions.set_table_metadata(table=table, metadata=metadata)

            try:
                self._assign_table_holder(user=request.user, table=table)
            except ValueError as e:
                # Ensure the user is assigned as the table holder
                self._assign_table_holder(user=request.user, table=table)
                raise APIError(
                    "Table was created without embargo due to an unexpected "
                    "error during embargo setup."
                    f"{e}"
                )

        else:
            table_object = self.oep_create_table_transaction(
                table=table,
                schema=schema,
                column_definitions=column_definitions,
                constraint_definitions=constraint_definitions,
            )
            self._assign_table_holder(user=request.user, table=table)

            if metadata:
                actions.set_table_metadata(table=table, metadata=metadata)

    def _create_table_object(self, table: str):
        try:
            table_object = Table.objects.create(name=table)
        except IntegrityError:
            raise APIError("Table already exists")
        return table_object

    def _check_embargo_payload_valid(self, embargo_data):
        if not embargo_data:
            return None, False

        if not isinstance(embargo_data, dict):
            error = APIError("The embargo payload must be a dict")
            return error, False

        embargo_period = embargo_data.get("duration")
        if embargo_period in ["6_months", "1_year"]:
            # self._apply_embargo(table_object, embargo_period)
            return None, True
        elif embargo_period == "none":
            return None, False
        else:
            error = actions.APIError(
                f"Could not parse the embargo period format: {embargo_period}. "
                "Please use {'embargo': {'duration':'6_months'} } or '1_year' to "
                "set the embargo or use 'none' to remove the embargo."
            )
            return error, False

    def _apply_embargo(self, table_object, embargo_period):
        unpack_embargo_period = embargo_period.get("duration")
        duration_in_weeks = 26 if unpack_embargo_period == "6_months" else 52
        embargo, created = Embargo.objects.get_or_create(
            table=table_object,
            defaults={
                "duration": unpack_embargo_period,
                "date_ended": datetime.now() + timedelta(weeks=duration_in_weeks),
            },
        )
        if not created:
            if embargo.date_started:
                embargo.date_ended = embargo.date_started + timedelta(
                    weeks=duration_in_weeks
                )
            else:
                embargo.date_started = datetime.now()
                embargo.date_ended = embargo.date_started + timedelta(
                    weeks=duration_in_weeks
                )
            embargo.save()

    def _assign_table_holder(self, user, table: str):
        table_object = Table.load(name=table)
        perm, _ = login_models.UserPermission.objects.get_or_create(
            table=table_object, holder=user
        )
        perm.level = login_models.ADMIN_PERM
        perm.save()
        user.save()

    @api_exception
    @require_delete_permission
    def delete(self, request: Request, schema: str, table: str) -> JsonLikeResponse:
        orchestrator = TableCreationOrchestrator()

        schema, table = actions.get_table_name(schema, table)
        orchestrator.drop_table(schema=schema, table=table)

        return JsonResponse({}, status=status.HTTP_200_OK)


class ColumnAPIView(APIView):
    @api_exception
    @method_decorator(never_cache)
    def get(
        self, request: Request, schema: str, table: str, column: str | None = None
    ) -> JsonLikeResponse:
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
    def post(
        self, request: Request, schema: str, table: str, column: str
    ) -> JsonLikeResponse:
        schema, table = actions.get_table_name(schema, table)

        request_data_dict = get_request_data_dict(request)
        response = actions.column_alter(
            request_data_dict["query"], {}, schema, table, column
        )
        return JsonResponse(response)

    @api_exception
    @require_write_permission
    def put(
        self, request: Request, schema: str, table: str, column: str
    ) -> JsonLikeResponse:
        schema, table = actions.get_table_name(schema, table)
        request_data_dict = get_request_data_dict(request)
        actions.column_add(schema, table, column, request_data_dict["query"])
        return JsonResponse({}, status=201)


class FieldsAPIView(APIView):
    # TODO: is this really used?
    @method_decorator(never_cache)
    def get(
        self,
        request: Request,
        schema: str,
        table: str,
        column_id: int,
        column: str | None = None,
    ) -> JsonLikeResponse:
        schema, table = actions.get_table_name(schema, table, restrict_schemas=False)
        if (
            not parser.is_pg_qual(table)
            or not parser.is_pg_qual(schema)
            or not parser.is_pg_qual(column_id)
            or not parser.is_pg_qual(column)
        ):
            return ModJsonResponse({"error": "Bad Request", "http_status": 400})

        returnValue = actions.getValue(schema, table, column, column_id)
        if returnValue is None:
            return JsonResponse({}, status=404)
        else:
            return JsonResponse(returnValue, status=200)


class MovePublishAPIView(APIView):
    @api_exception
    @require_admin_permission
    def post(
        self, request: Request, schema: str, table: str, to_schema: str
    ) -> JsonLikeResponse:
        # Make payload more friendly as users tend to use the query wrapper in payload
        request_data_dict = get_request_data_dict(request)
        payload_query = request_data_dict.get("query", {})
        embargo_period = request_data_dict.get("embargo", {}).get(
            "duration", None
        ) or payload_query.get("embargo", {}).get("duration", None)
        actions.move_publish(schema, table, to_schema, embargo_period)

        return JsonResponse({}, status=status.HTTP_200_OK)


class TableUnpublishAPIView(APIView):
    @api_exception
    @require_admin_permission
    def post(self, request: HttpRequest, schema: str, table: str) -> JsonLikeResponse:
        """Set table to `not published`"""
        table_obj = Table.objects.get(name=table)
        table_obj.is_publish = False
        table_obj.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class MoveAPIView(APIView):
    @api_exception
    @require_admin_permission
    def post(
        self, request: Request, schema: str, table: str, to_schema: str
    ) -> JsonLikeResponse:
        actions.move(schema, table, to_schema)
        return JsonResponse({}, status=status.HTTP_200_OK)


class RowsAPIView(APIView):
    @api_exception
    @method_decorator(never_cache)
    def get(
        self, request: Request, schema: str, table: str, row_id: int | None = None
    ) -> JsonLikeResponse:
        if check_embargo(schema, table):
            return JsonResponse(
                {"error": "Access to this table is restricted due to embargo."},
                status=403,
            )

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
                where_clauses = conjunction([clause, where_clauses])
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
            response["Content-Disposition"] = (
                'attachment; filename="{schema}__{table}.csv"'.format(
                    schema=schema, table=table
                )
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
            django_table = Table.load(name=table)
            if django_table and django_table.oemetadata:
                zf.writestr(
                    "datapackage.json",
                    json.dumps(django_table.oemetadata).encode("utf-8"),
                )
            else:
                zf.writestr(
                    "datapackage.json",
                    json.dumps(OEMETADATA_LATEST_TEMPLATE).encode("utf-8"),
                )
            response = OEPStream(
                (chunk for chunk in zf),
                content_type="application/zip",
                session=session,
            )
            response["Content-Disposition"] = (
                'attachment; filename="{schema}__{table}.zip"'.format(
                    schema=schema, table=table
                )
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
    def post(
        self,
        request: Request,
        schema: str,
        table: str,
        row_id: int | None = None,
        action: str | None = None,
    ) -> JsonLikeResponse:
        if check_embargo(schema, table):
            return JsonResponse(
                {"error": "Access to this table is restricted due to embargo."},
                status=403,
            )

        schema, table = actions.get_table_name(schema, table)
        request_data_dict = get_request_data_dict(request)
        payload_query = request_data_dict["query"]
        status_code = status.HTTP_200_OK
        if row_id:
            response = self.__update_rows(request, schema, table, payload_query, row_id)
        else:
            if action == "new":
                response = self.__insert_row(
                    request, schema, table, payload_query, row_id
                )
                status_code = status.HTTP_201_CREATED
            else:
                response = self.__update_rows(
                    request, schema, table, payload_query, None
                )
        actions.apply_changes(schema, table)
        return stream(response, status_code=status_code)

    @api_exception
    @require_write_permission
    def put(
        self,
        request: Request,
        schema: str,
        table: str,
        row_id: int | None = None,
        action: str | None = None,
    ) -> JsonLikeResponse:
        if check_embargo(schema, table):
            return JsonResponse(
                {"error": "Access to this table is restricted due to embargo."},
                status=403,
            )

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

        request_data_dict = get_request_data_dict(request)
        payload_query = request_data_dict["query"]

        if row_id and payload_query.get("id", int(row_id)) != int(row_id):
            raise APIError(
                "Id in URL and query do not match. Ids may not change.",
                status=status.HTTP_409_CONFLICT,
            )

        engine = _get_engine()
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
            response = self.__update_rows(request, schema, table, payload_query, row_id)
            actions.apply_changes(schema, table)
            return JsonResponse(response)
        else:
            result = self.__insert_row(request, schema, table, payload_query, row_id)
            actions.apply_changes(schema, table)
            return JsonResponse(result, status=status.HTTP_201_CREATED)

    @api_exception
    @require_delete_permission
    def delete(
        self, request: Request, table: str, schema: str, row_id: int | None = None
    ) -> JsonLikeResponse:
        if check_embargo(schema, table):
            return JsonResponse(
                {"error": "Access to this table is restricted due to embargo."},
                status=403,
            )

        schema, table = actions.get_table_name(schema, table)
        result = self.__delete_rows(request, schema, table, row_id)
        actions.apply_changes(schema, table)
        return JsonResponse(result)

    @load_cursor()
    def __delete_rows(
        self, request: Request, schema: str, table: str, row_id: int | None = None
    ):
        if check_embargo(schema, table):
            return JsonResponse(
                {"error": "Access to this table is restricted due to embargo."},
                status=403,
            )

        where = request.GET.getlist("where")
        query: dict[str, str | list | dict] = {"schema": schema, "table": table}
        if where:
            query["where"] = self.__read_where_clause(where)

        request_data_dict = get_request_data_dict(request)
        context = {
            "connection_id": request_data_dict["connection_id"],
            "cursor_id": request_data_dict["cursor_id"],
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

    def __read_where_clause(self, wheres) -> list:
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
    def __insert_row(
        self,
        request: Request,
        schema: str,
        table: str,
        row,
        row_id: int | None = None,
    ):
        if row_id and row.get("id", int(row_id)) != int(row_id):
            return actions._response_error(
                "The id given in the query does not " "match the id given in the url"
            )
        if row_id:
            row["id"] = row_id

        request_data_dict = get_request_data_dict(request)
        context = {
            "connection_id": request_data_dict["connection_id"],
            "cursor_id": request_data_dict["cursor_id"],
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
    def __update_rows(
        self,
        request: Request,
        schema: str,
        table: str,
        row,
        row_id: int | None = None,
    ) -> dict:
        if check_embargo(schema, table):
            raise APIError(
                "Access to this table is restricted due to embargo.",
                status=403,
            )

        request_data_dict = get_request_data_dict(request)
        context = {
            "connection_id": request_data_dict["connection_id"],
            "cursor_id": request_data_dict["cursor_id"],
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
    def __get_rows(self, request: Request, data):
        table = actions._get_table(data["schema"], table=data["table"])
        columns = data.get("columns")

        if not columns:
            query = table.select()
        else:
            columns = [actions.get_column_obj(table, c) for c in columns]
            query = actions.get_columns_select(columns=columns)

        where_clauses = data.get("where")

        if where_clauses:
            query = query.where(parser.parse_condition(where_clauses))
            query = query_typecast_select(query)  # TODO: fix type hints in a better way

        orderby = data.get("orderby")
        if orderby:
            if isinstance(orderby, list):
                query = query.order_by(*map(parser.parse_expression, orderby))
            elif isinstance(orderby, str):
                query = query.order_by(orderby)
            else:
                raise APIError("Unknown order_by clause: " + orderby)
            query = query_typecast_select(query)  # TODO: fix type hints in a better way

        limit = data.get("limit")
        if limit and limit.isdigit():
            query = query.limit(int(limit))
            query = query_typecast_select(query)  # TODO: fix type hints in a better way

        offset = data.get("offset")
        if offset and offset.isdigit():
            query = query.offset(int(offset))
            query = query_typecast_select(query)  # TODO: fix type hints in a better way

        cursor = sessions.load_cursor_from_context(request.data)
        actions._execute_sqla(query, cursor)


class AdvancedFetchAPIView(APIView):
    @api_exception
    def post(self, request: Request, fetchtype) -> JsonLikeResponse:
        if fetchtype == "all":
            return self.do_fetch(request, actions.fetchall)
        elif fetchtype == "many":
            return self.do_fetch(request, actions.fetchmany)
        else:
            raise APIError("Unknown fetchtype: %s" % fetchtype)

    def do_fetch(self, request: Request, fetch):
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


class AdvancedCloseAllAPIView(LoginRequiredMixin, APIView):
    @api_exception
    def get(self, request: Request) -> JsonLikeResponse:
        sessions.close_all_for_user(request.user)
        return JsonResponse({"message": "All connections closed"})


@api_exception
def users_api_view(request: Request) -> JsonLikeResponse:
    query = request.GET.get("name", "")

    # Ensure query is not empty to proceed with filtering
    if query:
        users = (
            login_models.myuser.objects.annotate(
                similarity=TrigramSimilarity("name", query),
            )
            .filter(
                Q(similarity__gt=0.2) | Q(name__istartswith=query),
            )
            .order_by("-similarity")[:6]
        )
    else:
        # Returning an empty list.
        users = login_models.myuser.objects.none()

    # Convert to list of user names
    user_names = [user.name for user in users]

    return JsonResponse(user_names, safe=False)


@api_exception
def groups_api_view(request: Request) -> JsonLikeResponse:
    """
    Return all Groups where this user is a member that match
    the current query. The query is input by the User.
    """
    try:
        user = login_models.myuser.objects.get(id=request.user.id)
    except login_models.myuser.DoesNotExist:
        raise Http404

    query = request.GET.get("name", None)
    if not query:
        return JsonResponse([], safe=False)

    user_groups = user.memberships.all().prefetch_related(  # type:ignore related
        "group"
    )
    groups = [g.group for g in user_groups]

    # Assuming 'name' is the field you want to search against
    similar_groups = (
        login_models.Group.objects.annotate(
            similarity=TrigramSimilarity("name", query),
        )
        .filter(
            similarity__gt=0.2,  # Adjust the threshold as needed
            id__in=[group.id for group in groups],
        )
        .order_by("-similarity")[:5]
    )

    group_names = [group.name for group in similar_groups]

    return JsonResponse(group_names, safe=False)


@api_exception
def oeo_search_api_view(request: Request) -> JsonLikeResponse:
    if USE_LOEP:
        # get query from user request # TODO validate input to prevent sneaky stuff
        query = request.GET["query"]
        # call local search service
        # "http://loep/lookup-application/api/search?query={query}"
        url = f"{DBPEDIA_LOOKUP_SPARQL_ENDPOINT_URL}{query}"
        res = requests.get(url).json()
        # res: something like [{"label": "testlabel", "resource": "testresource"}]
        # send back to client
    else:
        raise APIError(
            "The endpoint for LOEP is not setup. Please contact a server admin."
        )
    return JsonResponse(res, safe=False)


class OekgSparqlAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> JsonLikeResponse:
        request_data_dict = get_request_data_dict(request)
        payload_query = request_data_dict.get("query", "")
        response_format = request_data_dict.get("format", "json")  # Default format

        if not validate_public_sparql_query(payload_query):
            raise ValidationError(
                "Invalid SPARQL query. Update/delete queries are not allowed."
            )

        try:
            content, content_type = execute_sparql_query(payload_query, response_format)
        except ValueError as e:
            raise ValidationError(str(e))

        if content_type == "application/sparql-results+json":
            return Response(content)
        else:
            return Response(content, content_type=content_type)


@api_exception
def oevkg_search_api_view(request: Request) -> JsonLikeResponse:
    if USE_ONTOP and ONTOP_SPARQL_ENDPOINT_URL:
        # get query from user request # TODO validate input to prevent sneaky stuff
        try:
            query = request.body.decode("utf-8")
        except UnicodeDecodeError:
            raise APIError("Invalid request body encoding. Please use 'utf-8'.")
        headers = {
            "Accept": "application/sparql-results+json",
            "Content-Type": "application/sparql-query",
        }
        # call local search service
        try:
            response = requests.post(
                ONTOP_SPARQL_ENDPOINT_URL, data=query, headers=headers
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise APIError(f"Error contacting SPARQL endpoint: {str(e)}")

        # res: something like [{"label": "testlabel", "resource": "testresource"}]
        # Maybe validate using shacl or other data model descriptor file
        try:
            res = response.json()
        except json.JSONDecodeError:
            raise APIError("Error decoding SPARQL endpoint response.")
    else:
        raise APIError(
            "The SPARQL endpoint for OEVKG is not setup. Please contact your server admin."  # noqa
        )
    # send back to client
    return JsonResponse(res, safe=False)


# Energyframework, Energymodel
@method_decorator(never_cache, name="dispatch")
class EnergyframeworkFactsheetListAPIView(generics.ListAPIView):
    """
    Used for the scenario bundles react app to be able to select a existing
    framework or model factsheet.
    """

    queryset = Energyframework.objects.all()
    serializer_class = EnergyframeworkSerializer


@method_decorator(never_cache, name="dispatch")
class EnergymodelFactsheetListAPIView(generics.ListAPIView):
    """
    Used for the scenario bundles react app to be able to select a existing
    framework or model factsheet.
    """

    queryset = Energymodel.objects.all()
    serializer_class = EnergymodelSerializer


@method_decorator(never_cache, name="dispatch")
class ScenarioDataTablesListAPIView(generics.ListAPIView):
    """
    Used for the scenario bundles react app to be able to populate
    form select options with existing datasets from scenario topic.
    """

    queryset = Table.objects.filter(topics__name="scenario")
    serializer_class = ScenarioDataTablesSerializer


class ManageOekgScenarioDatasetsAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Require authentication

    @api_exception
    @post_only_if_user_is_owner_of_scenario_bundle
    def post(self, request: Request) -> JsonLikeResponse:
        serializer = ScenarioBundleScenarioDatasetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            dataset_configs = get_dataset_configs(serializer.validated_data)
            response_data = process_datasets_sparql_query(dataset_configs)
        except APIError as e:
            return Response({"error": str(e)}, status=e.status)
        except Exception:
            return Response({"error": "An unexpected error occurred."}, status=500)

        if "error" in response_data:
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        return Response(response_data, status=status.HTTP_200_OK)


@api_exception
def table_approx_row_count_view(
    request: HttpRequest, table: str, schema: str | None = None
) -> JsonResponse:
    table_obj = Table.objects.get(name=table)
    precise_below = int(
        request.GET.get("precise-below", APPROX_ROW_COUNT_DEFAULT_PRECISE_BELOW)
    )
    approx_row_count = table_get_approx_row_count(
        table=table_obj, precise_below=precise_below
    )
    response = {"data": [[approx_row_count]]}
    return JsonResponse(response)


class TableSizeAPIView(APIView):
    """
    GET /api/v0/db/table-sizes/?schema=<schema>&table=<table>
    - schema+table -> single relation (detailed)
    - schema only  -> all tables in that schema (whitelisted)
    - none         -> all tables in whitelist
    """

    @api_exception
    def get(self, request: Request) -> JsonLikeResponse:
        table = request.query_params.get("table")

        if table:
            data = actions.get_single_table_size(table=table)
            if not data:
                raise APIError(f"Relation {table} not found.", status=404)
            return Response(data)

        # list mode
        data = actions.list_table_sizes()
        return Response(data, status=status.HTTP_200_OK)


AdvancedSearchAPIView = create_ajax_handler(
    actions.data_search, allow_cors=True, requires_cursor=True
)
AdvancedInsertAPIView = create_ajax_handler(actions.data_insert, requires_cursor=True)
AdvancedDeleteAPIView = create_ajax_handler(actions.data_delete, requires_cursor=True)
AdvancedUpdateAPIView = create_ajax_handler(actions.data_update, requires_cursor=True)
AdvancedInfoAPIView = create_ajax_handler(actions.data_info)
AdvancedHasSchemaAPIView = create_ajax_handler(actions.has_schema)
AdvancedHasTableAPIView = create_ajax_handler(actions.has_table)
AdvancedHasSequenceAPIView = create_ajax_handler(actions.has_sequence)
AdvancedHasTypeAPIView = create_ajax_handler(actions.has_type)
AdvancedGetSchemaNamesAPIView = create_ajax_handler(actions.get_schema_names)
AdvancedGetTableNamesAPIView = create_ajax_handler(actions.get_table_names)
AdvancedGetViewNamesAPIView = create_ajax_handler(actions.get_view_names)
AdvancedGetViewDefinitionAPIView = create_ajax_handler(actions.get_view_definition)
AdvancedGetColumnsAPIView = create_ajax_handler(actions.get_columns)
AdvancedGetPkConstraintAPIView = create_ajax_handler(actions.get_pk_constraint)
AdvancedGetForeignKeysAPIView = create_ajax_handler(actions.get_foreign_keys)
AdvancedGetIndexesAPIView = create_ajax_handler(actions.get_indexes)
AdvancedGetUniqueConstraintsAPIView = create_ajax_handler(
    actions.get_unique_constraints
)
AdvancedConnectionOpenAPIView = create_ajax_handler(actions.open_raw_connection)
AdvancedConnectionCloseAPIView = create_ajax_handler(actions.close_raw_connection)
AdvancedConnectionCommitAPIView = create_ajax_handler(actions.commit_raw_connection)
AdvancedConnectionRollbackAPIView = create_ajax_handler(actions.rollback_raw_connection)
AdvancedCursorOpenAPIView = create_ajax_handler(actions.open_cursor)
AdvancedCursorCloseAPIView = create_ajax_handler(actions.close_cursor)
AdvancedCursorFetchOneAPIView = create_ajax_handler(actions.fetchone)
AdvancedSetIsolationLevelAPIView = create_ajax_handler(actions.set_isolation_level)
AdvancedGetIsolationLevelAPIView = create_ajax_handler(actions.get_isolation_level)
AdvancedDoBeginTwophaseAPIView = create_ajax_handler(actions.do_begin_twophase)
AdvancedDoPrepareTwophaseAPIView = create_ajax_handler(actions.do_prepare_twophase)
AdvancedDoRollbackTwophaseAPIView = create_ajax_handler(actions.do_rollback_twophase)
AdvancedDoCommitTwophaseAPIView = create_ajax_handler(actions.do_commit_twophase)
AdvancedDoRecoverTwophaseAPIView = create_ajax_handler(actions.do_recover_twophase)
