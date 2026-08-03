"""API views

Guideline for Developers

- all module items should be either
  - name_api_view functions or
  - NAME_APIView classes
- all name_api_view or get/post/put/delete/patch methods of NAME_APIView classes
  must be @api_exception decorated (as outermost decorator)
- all must return a JSONLikeResponse
- all endpoitns that refer to a table action need to do a require_*_permission to
  check for the existance of a tabel object, pre-fetch it and check permission level

"""

__licence__ = """
SPDX-License-Identifier: AGPL-3.0-or-later

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
"""  # noqa: 501

import csv
import itertools
import json
import logging
import re
import time
from copy import deepcopy

import geoalchemy2  # noqa:F401 Although this import seems unused is has to be here
import requests
import zipstream
from django.conf import settings as django_settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q
from django.http import Http404, HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from oemetadata.latest.example import OEMETADATA_LATEST_EXAMPLE
from oemetadata.latest.template import OEMETADATA_LATEST_TEMPLATE
from rest_framework import generics, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

import login.models as login_models
from api import bulk_upload_guard, sessions
from api.actions import (
    apply_changes,
    bulk_upload_csv,
    close_cursor,
    close_raw_connection,
    column_add,
    column_alter,
    commit_raw_connection,
    data_delete,
    data_insert,
    data_search,
    data_update,
    describe_columns,
    describe_constraints,
    describe_indexes,
    do_begin_twophase,
    do_commit_twophase,
    do_prepare_twophase,
    do_recover_twophase,
    do_rollback_twophase,
    execute_sqla,
    fetchall,
    fetchmany,
    fetchone,
    get_column_obj,
    get_columns,
    get_columns_select,
    get_foreign_keys,
    get_indexes,
    get_isolation_level,
    get_pk_constraint,
    get_response_dict,
    get_schema_names,
    get_single_table_size,
    get_table_names,
    get_unique_constraints,
    get_view_definition,
    get_view_names,
    has_schema,
    has_table,
    list_table_sizes,
    move_publish,
    open_cursor,
    open_raw_connection,
    queue_column_change,
    queue_constraint_change,
    response_error,
    rollback_raw_connection,
    set_isolation_level,
    set_table_metadata,
    table_get_approx_row_count,
    table_has_row_with_id,
    translate_fetched_cell,
    try_convert_metadata_to_v2,
    try_parse_metadata,
    try_validate_metadata,
)
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
    sync_api_metadata_columns,
    update_tags_from_keywords,
)
from api.parser import (
    is_pg_qual,
    parse_condition,
    parse_expression,
    parse_scolumnd_from_columnd,
    query_typecast_select,
)
from api.serializers import (
    DatasetAssignTablesSerializer,
    DatasetCreateSerializer,
    DatasetReadSerializer,
    DatasetResourceSerializer,
    EnergyframeworkSerializer,
    EnergymodelSerializer,
    ScenarioBundleScenarioDatasetSerializer,
    ScenarioDataTablesSerializer,
)
from api.services.dataset_creation import (
    DatasetNameTaken,
    assemble_dataset_metadata,
    assign_table,
    create_dataset,
    user_may_assign_table,
)
from api.services.embargo import (
    EmbargoValidationError,
    apply_embargo,
    parse_embargo_payload,
)
from api.utils import (
    get_dataset_configs,
    get_or_403,
    request_data_dict,
    strip_query,
    table_or_404,
)
from api.validators.column import validate_column_names
from api.validators.identifier import (
    assert_valid_table_name,
)
from dataedit.models import BulkLoadEvent, Dataset, Table
from factsheet.permission_decorator import post_only_if_user_is_owner_of_scenario_bundle
from modelview.models import Energyframework, Energymodel
from oekg.utils import (
    execute_sparql_query,
    process_datasets_sparql_query,
    validate_public_sparql_query,
)
from oeplatform.settings import (
    APPROX_ROW_COUNT_DEFAULT_PRECISE_BELOW,
    DBPEDIA_LOOKUP_SPARQL_ENDPOINT_URL,
    IS_TEST,
    ONTOP_SPARQL_ENDPOINT_URL,
    TOPIC_SCENARIO,
    USE_LOEP,
    USE_ONTOP,
)

DBPEDIA_LOOKUP_SPARQL_ENDPOINT_URL_WO_QUERY = strip_query(
    DBPEDIA_LOOKUP_SPARQL_ENDPOINT_URL
)

logger = logging.getLogger("oeplatform")


@extend_schema_view(
    get=extend_schema(tags=["Schema: Meta"]),
    post=extend_schema(tags=["Schema: Meta"]),
)
class TableMetadataAPIView(APIView):
    """
    Important note:
    oemetadata v2 introduces datasets which are not relevant on a table level
    always query for metadata["resources"][0]. Keeping the complete oemetadata v2 JSON
    makes it easy to integrate as no further changes to validation are required for now.
    Datasets are handled in the model.Datasets & api views.
    """

    @api_exception
    @method_decorator(never_cache)
    def get(self, request: Request, table: str) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)
        metadata = table_obj.get_metadata()
        return JsonResponse(metadata)

    @api_exception
    @require_write_permission
    @load_cursor()
    def post(self, request: Request, table: str) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)

        raw_input = request.data
        metadata, error = try_parse_metadata(raw_input)

        if not error and metadata is not None:
            metadata = try_convert_metadata_to_v2(metadata)

            # Enforce database schema and clean artifacts
            metadata = sync_api_metadata_columns(metadata, table_obj)

            # Now validate the beautifully cleaned and synced metadata
            metadata, error = try_validate_metadata(metadata)

        if metadata is not None:
            # update/sync keywords with tags before saving metadata
            # oemetadata v2 introduces datasets which are not relevant on a table level
            # always query for metadata["resources"][0]

            keywords = metadata["resources"][0].get("keywords", []) or []
            metadata["resources"][0]["keywords"] = update_tags_from_keywords(
                table=table_obj.name, keywords=keywords
            )

            # make sure extra metadata is removed
            metadata.pop("connection_id", None)
            metadata.pop("cursor_id", None)

            # Save the reconciled metadata to the database
            set_table_metadata(table=table_obj.name, metadata=metadata)

            # Return the cleaned metadata
            return JsonResponse(metadata)
        else:
            raise APIError(error)


@extend_schema_view(
    post=extend_schema(
        summary="Create dataset",
        description="Creates a new dataset.",
        request=DatasetCreateSerializer,
        responses={},
        examples=[
            OpenApiExample(
                "Dataset Example",
                summary="Example request body for " "creating a dataset",
                description=(
                    "Use this JSON object to create a new dataset. "
                    "The `at_id` field is optional and can contain "
                    "a persistent identifier."
                ),
                value={
                    "name": "test_dataset",
                    "title": "Wind Power Dataset Germany",
                    "description": (
                        "Contains hourly wind generation " "data for Germany."
                    ),
                    "at_id": "https://example.org/datasets/test_dataset",
                },
                request_only=True,
            )
        ],
    )
)
def assert_dataset_ownership(user, dataset: Dataset) -> None:
    """Datasets are creator-owned: only the creator may modify one."""
    if dataset.creator is None or dataset.creator != user:
        raise PermissionDenied("Only the dataset creator may modify this dataset.")


def load_owned_dataset_from_request(request, dataset_name: str):
    """Shared prologue of the dataset membership endpoints: validate the
    table list, load the dataset and enforce ownership.

    Returns (dataset, table_refs) or (error_response, None) when the
    dataset does not exist.
    """
    serializer = DatasetAssignTablesSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        dataset = Dataset.objects.get(name=dataset_name)
    except Dataset.DoesNotExist:
        return (
            Response({"error": "Dataset not found"}, status=status.HTTP_404_NOT_FOUND),
            None,
        )

    assert_dataset_ownership(request.user, dataset)
    return dataset, serializer.validated_data["tables"]


class DatasetsListCreate(generics.ListCreateAPIView):
    queryset = Dataset.objects.prefetch_related("tables")
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DatasetCreateSerializer
        return DatasetReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            dataset = create_dataset(serializer.validated_data, creator=request.user)
        except DatasetNameTaken as error:
            raise ValidationError({"name": str(error)})

        return Response(
            {
                "id": dataset.pk,
                "metadata": DatasetReadSerializer(dataset).data["metadata"],
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(
        summary="List dataset resources",
        description="Returns the tables/resources that belong to a dataset.",
        responses=DatasetResourceSerializer(many=True),
    )
)
class DatasetsListResources(generics.ListAPIView):
    serializer_class = DatasetResourceSerializer

    def get_queryset(self):
        dataset_name = self.kwargs["dataset_name"]
        dataset = get_object_or_404(Dataset, name=dataset_name)
        return dataset.tables.all()


@extend_schema_view(
    get=extend_schema(
        summary="Get dataset",
        description="Returns metadata for a single dataset.",
        responses=DatasetReadSerializer,
    ),
    put=extend_schema(
        summary="Update dataset",
        description="Updates metadata for an existing dataset.",
        request=DatasetCreateSerializer,
        responses={200: OpenApiResponse(description="Dataset updated")},
        examples=[
            OpenApiExample(
                "Update dataset example",
                summary="Example request body for updating a dataset",
                value={
                    "name": "test_dataset",
                    "title": "Updated Wind Power Dataset Germany",
                    "description": "Updated description with more details.",
                    "at_id": "https://example.org/datasets/test_dataset",
                },
                request_only=True,
            )
        ],
    ),
    delete=extend_schema(
        summary="Delete dataset",
        description="Deletes the specified dataset.",
        responses={204: OpenApiResponse(description="Dataset deleted")},
    ),
)
class DatasetManager(APIView):
    """
    View to retrieve, update, or delete a single dataset's metadata.
    URL: /v0/datasets/<dataset_name>/
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, dataset_name):
        dataset = get_object_or_404(Dataset, name=dataset_name)
        serializer = DatasetReadSerializer(dataset)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, dataset_name):
        dataset = get_object_or_404(Dataset, name=dataset_name)
        assert_dataset_ownership(request.user, dataset)
        serializer = DatasetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data["name"] != dataset.name:
            raise ValidationError(
                {"name": "The dataset name is fixed at creation and can not change."}
            )

        dataset.metadata = assemble_dataset_metadata(serializer.validated_data)
        dataset.save()
        return Response({"message": "Dataset updated"}, status=status.HTTP_200_OK)

    def delete(self, request, dataset_name):
        dataset = get_object_or_404(Dataset, name=dataset_name)
        assert_dataset_ownership(request.user, dataset)
        dataset.delete()
        return Response(
            {"message": "Dataset deleted"},
            status=status.HTTP_204_NO_CONTENT,
        )


class AssignDatasetTables(APIView):
    """
    Assign existing OEP tables to an existing dataset.
    """

    @extend_schema(
        summary="Assign tables to dataset",
        description=(
            "Assigns existing OEP tables to an existing dataset. "
            "The dataset must already exist and the referenced "
            "tables must already exist. After assignment, the "
            "dataset resources are updated from the table metadata."
        ),
        parameters=[
            OpenApiParameter(
                name="dataset_name",
                type=str,
                location=OpenApiParameter.PATH,
                required=True,
                description=(
                    "Name of the dataset to which the tables should be assigned. "
                    "Example: `test_dataset`."
                ),
            )
        ],
        request=DatasetAssignTablesSerializer,
        responses={
            200: OpenApiResponse(description="Tables were assigned to the dataset."),
            404: OpenApiResponse(description="Dataset was not found."),
        },
        examples=[
            OpenApiExample(
                "Assign tables example",
                summary="Example request body for assigning tables",
                value={
                    "tables": [
                        {"name": "germany_wind_hourly"},
                        {"name": "germany_wind_daily"},
                    ]
                },
                request_only=True,
            )
        ],
    )
    def post(self, request, dataset_name):
        serializer = DatasetAssignTablesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        table_refs = serializer.validated_data["tables"]
    permission_classes = [IsAuthenticated]

    def post(self, request, dataset_name):
        dataset, table_refs = load_owned_dataset_from_request(request, dataset_name)
        if table_refs is None:
            return dataset

        missing = []
        tables = []

        for table_ref in table_refs:
            try:
                tables.append(Table.load(table_ref["name"]))
            except Table.DoesNotExist:
                missing.append(table_ref)

        forbidden = [
            table.name
            for table in tables
            if not user_may_assign_table(request.user, table)
        ]
        if forbidden:
            raise PermissionDenied(
                "Draft or embargoed tables require write permission on the "
                f"table to be assigned: {', '.join(forbidden)}."
            )

        added_tables = []
        for table in tables:
            assign_table(dataset, table)
            added_tables.append(table.name)

        return Response(
            {
                "message": f"Added {len(added_tables)} tables.",
                "added": added_tables,
                "missing": missing,
            },
            status=status.HTTP_200_OK,
        )


class UnassignDatasetTables(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, dataset_name):
        dataset, table_refs = load_owned_dataset_from_request(request, dataset_name)
        if table_refs is None:
            return dataset

        missing = []
        removed_tables = []

        for table_ref in table_refs:
            table = dataset.tables.filter(name=table_ref["name"]).first()
            if table is None:
                missing.append(table_ref)
            else:
                dataset.tables.remove(table)
                removed_tables.append(table.name)

        return Response(
            {
                "message": f"Removed {len(removed_tables)} tables.",
                "removed": removed_tables,
                "missing": missing,
            },
            status=status.HTTP_200_OK,
        )


class TableAPIView(APIView):
    """
    Handles the creation of tables and serves information on existing tables
    """

    objects = None

    @api_exception
    @method_decorator(never_cache)
    def get(self, request: Request, table: str) -> JsonLikeResponse:
        """
        Returns a dictionary that describes the DDL-make-up of this table.
        Fields are:

        * name : Name of the table,
        * columns : as specified in :meth:`api.actions.describe_columns`
        * indexes : as specified in :meth:`api.actions.describe_indexes`
        * constraints: as specified in
                    :meth:`api.actions.describe_constraints`

        :param request:
        :return:
        """
        table_obj = table_or_404(table=table)

        return JsonResponse(
            {
                "name": table,
                "columns": describe_columns(table_obj),
                "indexed": describe_indexes(table_obj),
                "constraints": describe_constraints(table_obj),
            }
        )

    @api_exception
    def post(self, request: Request, table: str) -> JsonLikeResponse:
        """
        Changes properties of tables and table columns
        :param request:
        :param table:
        :return:
        """
        table_obj = table_or_404(table=table)

        request_data_dict = get_request_data_dict(request)

        if "column" in request_data_dict["type"]:
            column_definition = parse_scolumnd_from_columnd(
                table_obj, request_data_dict["name"], request_data_dict
            )
            result = queue_column_change(table_obj, column_definition)
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

            result = queue_constraint_change(table_obj, constraint_definition)
            return ModJsonResponse(result)
        else:
            return ModJsonResponse(get_response_dict(False, 400, "type not recognised"))

    @api_exception
    def put(self, request: Request, table: str) -> JsonLikeResponse:
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
            table: The name of the table to be created

        Returns:
            JsonResponse: A JSON response with the status code 201 CREATED

        """

        # 1) Basic checks
        if request.user.is_anonymous:
            raise APIError("User is anonymous", 401)

        # during tests, is_sandbox must be true
        # otherwise: can be set as ?is_sandbox=
        if IS_TEST or request.GET.get("is_sandbox"):
            is_sandbox = True
        else:
            is_sandbox = False

        # 2) Validate identifiers
        assert_valid_table_name(table)

        if has_table({"table": table}):
            raise APIError("Table already exists", 409)

        # 3) Parse and validate payload
        request_data_dict = get_request_data_dict(request)
        payload_query = request_data_dict.get("query", {})
        columns = payload_query.get("columns")
        if not columns:
            raise APIError("Table contains no columns")
        for col in columns:
            col.update({"c_table": table})
        validate_column_names(columns)

        constraints = payload_query.get("constraints", [])
        for cons in constraints:
            cons.update({"action": "ADD", "c_table": table})

        embargo_data = request_data_dict.get("embargo") or payload_query.get(
            "embargo", {}
        )
        try:
            embargo_required = parse_embargo_payload(embargo_data)
        except EmbargoValidationError as e:
            raise APIError(str(e))

        table_obj = Table.create_with_oedb_table(
            name=table,
            user=request.user,
            is_sandbox=is_sandbox,
            column_definitions=columns,
            constraints_definitions=constraints,
        )

        # 5) Post-creation hooks
        if embargo_required:
            apply_embargo(table_obj, embargo_data)

        metadata = payload_query.get("metadata")
        if metadata:
            set_table_metadata(table=table, metadata=metadata)
        else:
            # If no metadata is provided, we create a minimal metadata object
            metadata = deepcopy(OEMETADATA_LATEST_TEMPLATE)
            metadata["@context"] = OEMETADATA_LATEST_EXAMPLE["@context"]
            metadata["metaMetadata"] = OEMETADATA_LATEST_EXAMPLE["metaMetadata"]

            # Set basic resource info
            resource = {
                "name": table,
            }

            # Update the first resource - there will only be one resource.
            # The dataset section is managed by the database implementation ...
            metadata["resources"][0].update(resource)

            # Build schema fields from columns
            fields = []
            for col in columns:
                field = {
                    "name": col["name"],
                    "type": col["data_type"],
                    "nullable": col.get("is_nullable", True),
                    # add more field metadata as needed
                }
                fields.append(field)

            # Replace the fields list entirely
            metadata["resources"][0]["schema"]["fields"] = fields

            set_table_metadata(table=table, metadata=metadata)

        return JsonResponse({}, status=status.HTTP_201_CREATED)

    @api_exception
    @require_delete_permission
    def delete(self, request: Request, table: str) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)
        table_obj.delete()
        return JsonResponse({}, status=status.HTTP_200_OK)


class TableColumnAPIView(APIView):
    @api_exception
    @method_decorator(never_cache)
    def get(
        self, request: Request, table: str, column: str | None = None
    ) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)

        response = describe_columns(table_obj)
        if column:
            try:
                response = response[column]
            except KeyError:
                raise APIError("The column specified is not part of this table.")
        return JsonResponse(response)

    @api_exception
    @require_write_permission
    def post(self, request: Request, table: str, column: str) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)

        request_data_dict = get_request_data_dict(request)
        response = column_alter(request_data_dict["query"], table_obj, column)
        return JsonResponse(response)

    @api_exception
    @require_write_permission
    def put(self, request: Request, table: str, column: str) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)
        request_data_dict = get_request_data_dict(request)
        column_add(table_obj, column, request_data_dict["query"])
        return JsonResponse({}, status=201)


class TableMovePublishAPIView(APIView):
    @api_exception
    @require_admin_permission
    def post(self, request: Request, table: str, topic: str) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)

        # Make payload more friendly as users tend to use the query wrapper in payload
        request_data_dict = get_request_data_dict(request)
        payload_query = request_data_dict.get("query", {})
        embargo_period = request_data_dict.get("embargo", {}).get(
            "duration", None
        ) or payload_query.get("embargo", {}).get("duration", None)
        move_publish(table_obj, topic, embargo_period)

        return JsonResponse({}, status=status.HTTP_200_OK)


class TableUnpublishAPIView(APIView):
    @api_exception
    @require_admin_permission
    def post(self, request: HttpRequest, table: str) -> JsonLikeResponse:
        """Set table to `not published`"""
        table_obj = table_or_404(table=table)
        table_obj.is_publish = False
        table_obj.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class TableRowsAPIView(APIView):
    @api_exception
    @method_decorator(never_cache)
    def get(
        self, request: Request, table: str, row_id: int | None = None
    ) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)

        if check_embargo(table_obj):
            return JsonResponse(
                {"error": "Access to this table is restricted due to embargo."},
                status=403,
            )

        columns = request.GET.getlist("column")

        where = request.GET.getlist("where")
        if row_id and where:
            raise APIError("Where clauses and row id are not allowed in the same query")

        orderby = request.GET.getlist("orderby")
        if row_id and orderby:
            raise APIError(
                "Order by clauses and row id are not allowed in the same query"
            )

        limit = request.GET.get("limit")
        if row_id and limit:
            raise APIError(
                "Limit by clauses and row id are not allowed in the same query"
            )

        offset = request.GET.get("offset")
        if row_id and offset:
            raise APIError(
                "Order by clauses and row id are not allowed in the same query"
            )

        format = request.GET.get("form")

        if offset is not None and not offset.isdigit():
            raise APIError("Offset must be integer")
        if limit is not None and not limit.isdigit():
            raise APIError("Limit must be integer")
        if not all(is_pg_qual(c) for c in columns):
            raise APIError("Columns are no postgres qualifiers")
        if not all(is_pg_qual(c) for c in orderby):
            raise APIError("Columns in groupby-clause are no postgres qualifiers")

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
            "table": table,
            "columns": columns,
            "where": where_clauses,
            "orderby": orderby,
            "limit": limit,
            "offset": offset,
        }

        return_obj = self.__get_rows(request, table_obj, data)
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
            # in dataedit/static/database/backend.js: parse_download()
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
                'attachment; filename="{table}.csv"'.format(table=table)
            )
            return response
        elif format == "datapackage":
            pseudo_buffer = Echo()
            writer = csv.writer(pseudo_buffer, quoting=csv.QUOTE_ALL)
            zf = zipstream.ZipFile(mode="w", compression=zipstream.ZIP_DEFLATED)
            csv_name = "{table}.csv".format(table=table)
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
                'attachment; filename="{table}.zip"'.format(table=table)
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
        table: str,
        row_id: int | None = None,
        action: str | None = None,
    ) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)

        if check_embargo(table_obj):
            return JsonResponse(
                {"error": "Access to this table is restricted due to embargo."},
                status=403,
            )

        request_data_dict = get_request_data_dict(request)
        payload_query = request_data_dict["query"]
        status_code = status.HTTP_200_OK
        if row_id:
            response = self.__update_rows(request, table_obj, payload_query, row_id)
        else:
            if action == "new":
                response = self.__insert_row(request, table_obj, payload_query, row_id)
                status_code = status.HTTP_201_CREATED
            else:
                response = self.__update_rows(request, table_obj, payload_query, None)
        apply_changes(table_obj)
        return stream(response, status_code=status_code)

    @api_exception
    @require_write_permission
    def put(
        self,
        request: Request,
        table: str,
        row_id: int | None = None,
        action: str | None = None,
    ) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)

        if check_embargo(table_obj):
            return JsonResponse(
                {"error": "Access to this table is restricted due to embargo."},
                status=403,
            )

        if action:
            raise APIError(
                "This request type (PUT) is not supported. The "
                "'new' statement is only possible in POST requests."
            )

        if not row_id:
            return JsonResponse(
                response_error("This methods requires an id"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        row_id = int(row_id)

        request_data_dict = get_request_data_dict(request)
        payload_query = request_data_dict["query"]

        if payload_query.get("id", row_id) != row_id:
            raise APIError(
                "Id in URL and query do not match. Ids may not change.",
                status=status.HTTP_409_CONFLICT,
            )

        exists = table_has_row_with_id(table_obj, id=row_id) if row_id else False
        if exists:
            response = self.__update_rows(request, table_obj, payload_query, row_id)
            apply_changes(table_obj)
            return JsonResponse(response)
        else:
            result = self.__insert_row(request, table_obj, payload_query, row_id)
            apply_changes(table_obj)
            return JsonResponse(result, status=status.HTTP_201_CREATED)

    @api_exception
    @require_delete_permission
    def delete(
        self, request: Request, table: str, row_id: int | None = None
    ) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)

        if check_embargo(table_obj):
            return JsonResponse(
                {"error": "Access to this table is restricted due to embargo."},
                status=403,
            )

        result = self.__delete_rows(request, table_obj, row_id)
        apply_changes(table_obj)
        return JsonResponse(result)

    @load_cursor()
    def __delete_rows(
        self, request: Request, table_obj: Table, row_id: int | None = None
    ):
        if check_embargo(table_obj):
            return JsonResponse(
                {"error": "Access to this table is restricted due to embargo."},
                status=403,
            )

        where = request.GET.getlist("where")
        query: dict[str, str | list | dict] = {"table": table_obj.name}
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

        return data_delete(query, context)

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
        table_obj: Table,
        row,
        row_id: int | None = None,
    ):
        if row_id and row.get("id", int(row_id)) != int(row_id):
            return response_error(
                "The id given in the query does not match the id given in the url"
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
            "table": table_obj.name,
            "values": [row] if isinstance(row, dict) else row,
        }

        if not row_id:
            query["returning"] = [{"type": "column", "column": "id"}]
        result = data_insert(query, context)

        return result

    @load_cursor()
    def __update_rows(
        self,
        request: Request,
        table_obj: Table,
        row,
        row_id: int | None = None,
    ) -> dict:
        if check_embargo(table_obj):
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

        query = {"table": table_obj.name, "values": row}

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

        return data_update(query, context)

    @load_cursor(named=True)
    def __get_rows(self, request: Request, table_obj: Table, data):
        sa_table = table_obj.get_oedb_table_proxy()._main_table.get_sa_table()
        columns = data.get("columns")

        if not columns:
            query = sa_table.select()
        else:
            columns = [get_column_obj(sa_table, c) for c in columns]
            query = get_columns_select(columns=columns)

        where_clauses = data.get("where")

        if where_clauses:
            query = query.where(parse_condition(where_clauses))
            query = query_typecast_select(query)  # TODO: fix type hints in a better way

        orderby = data.get("orderby")
        if orderby:
            if isinstance(orderby, list):
                query = query.order_by(*map(parse_expression, orderby))
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

        cursor = sessions.load_cursor_from_context(request_data_dict(request))
        execute_sqla(query, cursor)


def _record_bulk_load_event(table_obj, user, status_value, **fields):
    """Write the audit record; never let a failure here mask the upload's
    actual outcome (the event is best-effort, the response is not)."""
    try:
        return BulkLoadEvent.objects.create(
            table_name=table_obj.name, user=user, status=status_value, **fields
        )
    except Exception:
        logger.exception(
            "failed to record bulk load event for table %s", table_obj.name
        )
        return None


bulk_upload_logger = logging.getLogger("oeplatform.bulk_upload")


def _log_bulk_upload_attempt(
    table_obj,
    user,
    outcome: str,
    total_seconds: float,
    bytes_received: int = 0,
    rows=None,
    timings: dict | None = None,
):
    """Exactly one structured (logfmt) line per bulk upload attempt.

    Format (fields never reordered; '-' when a value is not applicable):

        bulk_upload table=<name> user=<username> outcome=<outcome>
        rows=<n|-> bytes=<n> total_s=<s> transfer_s=<s|-> copy_s=<s|->
        setval_s=<s|->

    Outcomes: success, validation-error, copy-error, size-cap, stall,
    embargo, busy, error. Phase timings: transfer = client I/O incl.
    decompression, copy = database-side COPY work, setval = id-contract
    and id-range queries. This line plus the BulkLoadEvent table is the
    endpoint's shipped observability (dashboards/canary: ops follow-up).
    """
    timings = timings or {}

    def seconds(key):
        value = timings.get(key)
        return "-" if value is None else "%.3f" % value

    bulk_upload_logger.info(
        "bulk_upload table=%s user=%s outcome=%s rows=%s bytes=%d "
        "total_s=%.3f transfer_s=%s copy_s=%s setval_s=%s",
        table_obj.name,
        getattr(user, "name", None) or "-",
        outcome,
        rows if rows is not None else "-",
        bytes_received,
        total_seconds,
        seconds("transfer_s"),
        seconds("copy_s"),
        seconds("setval_s"),
    )


class TableBulkUploadAPIView(APIView):
    """Bulk Upload (issue #2362): the request body IS the CSV.

    Append-only, all-or-nothing; rows go directly into the main table
    without edit-journal records. The delimiter parameter is required.
    Every attempt that reaches the upload itself - i.e. authenticated,
    authorized, existing table, free guard slot - leaves a BulkLoadEvent,
    the upload's only provenance. Denials at the decorator level
    (401/403/404) and guard rejections (429) deliberately create no
    events: anonymous requests must not write database rows, and busy
    rejections are cheap pre-work denials. Every attempt reaching this
    endpoint body additionally emits one structured log line (see
    _log_bulk_upload_attempt for the format).
    """

    @api_exception
    @require_write_permission
    def post(self, request: Request, table: str) -> JsonLikeResponse:
        started = time.perf_counter()
        table_obj = table_or_404(table=table)

        if check_embargo(table_obj):
            _record_bulk_load_event(
                table_obj,
                request.user,
                BulkLoadEvent.STATUS_EMBARGO,
                error_message="Access to this table is restricted due to embargo.",
            )
            _log_bulk_upload_attempt(
                table_obj,
                request.user,
                BulkLoadEvent.STATUS_EMBARGO,
                time.perf_counter() - started,
            )
            return JsonResponse(
                {"error": "Access to this table is restricted due to embargo."},
                status=403,
            )

        gzipped = request.META.get("HTTP_CONTENT_ENCODING", "").strip().lower() in (
            "gzip",
            "x-gzip",  # legacy alias, RFC 9110
        )
        try:
            # guard: one running upload per user + global cap (ADR 0002);
            # rejections are cheap pre-work denials and create no event
            with bulk_upload_guard.guard.slot(request.user.id):
                stats = bulk_upload_csv(
                    table_obj,
                    request.stream,
                    request.GET.get("delimiter"),
                    gzipped=gzipped,
                    # read at request time (django.conf) so tests can override
                    max_bytes=django_settings.BULK_UPLOAD_MAX_BYTES,
                )
        except bulk_upload_guard.BulkUploadBusy as e:
            _log_bulk_upload_attempt(
                table_obj, request.user, "busy", time.perf_counter() - started
            )
            response = JsonResponse({"error": str(e)}, status=429)
            response["Retry-After"] = str(bulk_upload_guard.RETRY_AFTER_SECONDS)
            return response
        except APIError as e:
            outcome = getattr(e, "bulk_error_class", BulkLoadEvent.STATUS_ERROR)
            _record_bulk_load_event(
                table_obj,
                request.user,
                outcome,
                error_message=e.message,
                bytes_received=getattr(e, "bulk_bytes_received", 0),
            )
            _log_bulk_upload_attempt(
                table_obj,
                request.user,
                outcome,
                time.perf_counter() - started,
                bytes_received=getattr(e, "bulk_bytes_received", 0),
                timings=getattr(e, "bulk_timings", None),
            )
            raise
        except Exception:
            # unexpected failure (a bug, not a client error): still exactly
            # one event and one log line per attempt, then let it propagate
            _record_bulk_load_event(
                table_obj,
                request.user,
                BulkLoadEvent.STATUS_ERROR,
                error_message="unexpected error",
            )
            _log_bulk_upload_attempt(
                table_obj,
                request.user,
                BulkLoadEvent.STATUS_ERROR,
                time.perf_counter() - started,
            )
            raise

        event = _record_bulk_load_event(
            table_obj,
            request.user,
            BulkLoadEvent.STATUS_SUCCESS,
            bytes_received=stats["bytes_received"],
            row_count=stats["rows"],
            id_min=stats["id_min"],
            id_max=stats["id_max"],
        )
        _log_bulk_upload_attempt(
            table_obj,
            request.user,
            BulkLoadEvent.STATUS_SUCCESS,
            time.perf_counter() - started,
            bytes_received=stats["bytes_received"],
            rows=stats["rows"],
            timings=stats["timings"],
        )
        return JsonResponse(
            {
                "rows": stats["rows"],
                "event_id": event.id if event else None,
                "id_range": [stats["id_min"], stats["id_max"]],
            },
            status=status.HTTP_201_CREATED,
        )


@api_exception
@never_cache
def table_approx_row_count_view(request: HttpRequest, table: str) -> JsonResponse:
    table_obj = table_or_404(table=table)
    precise_below = int(
        request.GET.get("precise-below", APPROX_ROW_COUNT_DEFAULT_PRECISE_BELOW)
    )
    approx_row_count = table_get_approx_row_count(
        table=table_obj, precise_below=precise_below
    )
    response = {"data": [[approx_row_count]]}
    return JsonResponse(response)


@api_exception
@never_cache
def usrprop_api_view(request: Request) -> JsonLikeResponse:
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


@never_cache
@api_exception
def grpprop_api_view(request: Request) -> JsonLikeResponse:
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

    user_groups = user.memberships.all().prefetch_related("group")
    groups = [g.group for g in user_groups]

    # Assuming 'name' is the field you want to search against
    similar_groups = (
        login_models.Group.objects.annotate(
            similarity=TrigramSimilarity("name", query),
        )
        .filter(
            similarity__gt=0.2,  # Adjust the threshold as needed
            id__in=[group.pk for group in groups],
        )
        .order_by("-similarity")[:5]
    )

    group_names = [group.name for group in similar_groups]

    return JsonResponse(group_names, safe=False)


@never_cache
@api_exception
def oeo_search_api_view(request: Request) -> JsonLikeResponse:
    if USE_LOEP:
        # get query from user request # TODO validate input to prevent sneaky stuff
        query = request.GET["query"]
        # call local search service
        # "http://loep/lookup-application/api/search?query={query}"

        # NOTE: to pass snyk security review, user data (request.GET["query"])
        # put into request.get() is dangerous and needs to be secured by
        # clearly separating the base url
        url = f"{DBPEDIA_LOOKUP_SPARQL_ENDPOINT_URL_WO_QUERY}?query={query}"
        res = requests.get(url).json()
        # res: something like
        # {"docs": [{"label": "testlabel", "resource": "testresource"}]}
        # send back to client
    else:
        raise APIError(
            "The endpoint for LOEP is not setup. Please contact a server admin."
        )
    return JsonResponse(res, safe=False)


@never_cache
@api_exception
def oevkg_query_api_view(request: Request) -> JsonLikeResponse:
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


class OekgSparqlAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @api_exception
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

    queryset = Table.objects.filter(topics__name=TOPIC_SCENARIO)
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


class AllTableSizesAPIView(APIView):
    """
    GET /api/v0/db/table-sizes/?stopic=<stopic>&table=<table>
    - table -> single relation (detailed)
    - none  -> all tables
    """

    @api_exception
    @method_decorator(never_cache)
    def get(self, request: Request) -> JsonLikeResponse:
        table = request.query_params.get("table")

        if table:
            table_obj = table_or_404(table=table)
            data = get_single_table_size(table_obj=table_obj)
            if not data:
                raise APIError(f"Relation {table} not found.", status=404)
            return Response(data)

        # list mode
        data = list_table_sizes()
        return Response(data, status=status.HTTP_200_OK)


@extend_schema_view(post=extend_schema(tags=["Advanced: Cursor"]))
class AdvancedFetchAPIView(APIView):
    @api_exception
    def post(self, request: Request, fetchtype) -> JsonLikeResponse:
        if fetchtype == "all":
            return self.do_fetch(request, fetchall)
        elif fetchtype == "many":
            return self.do_fetch(request, fetchmany)
        else:
            raise APIError("Unknown fetchtype: %s" % fetchtype)

    def do_fetch(self, request: Request, fetch):
        data = request_data_dict(request)
        context = {
            "connection_id": get_or_403(data, "connection_id"),
            "cursor_id": get_or_403(data, "cursor_id"),
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
            [translate_fetched_cell(cell) for cell in row],
            default=date_handler,
        )


@extend_schema_view(get=extend_schema(tags=["Advanced: Connection"]))
class AdvancedCloseAllAPIView(LoginRequiredMixin, APIView):
    @api_exception
    def get(self, request: Request) -> JsonLikeResponse:
        sessions.close_all_for_user(request.user)
        return JsonResponse({"message": "All connections closed"})


AdvancedSearchAPIView = extend_schema_view(post=extend_schema(tags=["Advanced"]))(
    create_ajax_handler(data_search, allow_cors=True, requires_cursor=True)
)
AdvancedInsertAPIView = extend_schema_view(post=extend_schema(tags=["Advanced"]))(
    create_ajax_handler(data_insert, requires_cursor=True)
)
AdvancedDeleteAPIView = extend_schema_view(post=extend_schema(tags=["Advanced"]))(
    create_ajax_handler(data_delete, requires_cursor=True)
)
AdvancedUpdateAPIView = extend_schema_view(post=extend_schema(tags=["Advanced"]))(
    create_ajax_handler(data_update, requires_cursor=True)
)


AdvancedHasSchemaAPIView = extend_schema_view(post=extend_schema(tags=["Advanced"]))(
    create_ajax_handler(has_schema)
)
AdvancedHasTableAPIView = extend_schema_view(post=extend_schema(tags=["Advanced"]))(
    create_ajax_handler(has_table)
)
AdvancedGetSchemaNamesAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced"])
)(create_ajax_handler(get_schema_names))
AdvancedGetTableNamesAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced"])
)(create_ajax_handler(get_table_names))
AdvancedGetViewNamesAPIView = extend_schema_view(post=extend_schema(tags=["Advanced"]))(
    create_ajax_handler(get_view_names)
)
AdvancedGetViewDefinitionAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced"])
)(create_ajax_handler(get_view_definition))
AdvancedGetColumnsAPIView = extend_schema_view(post=extend_schema(tags=["Advanced"]))(
    create_ajax_handler(get_columns)
)
AdvancedGetPkConstraintAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced"])
)(create_ajax_handler(get_pk_constraint))
AdvancedGetForeignKeysAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced"])
)(create_ajax_handler(get_foreign_keys))
AdvancedGetIndexesAPIView = extend_schema_view(post=extend_schema(tags=["Advanced"]))(
    create_ajax_handler(get_indexes)
)
AdvancedGetUniqueConstraintsAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced"])
)(create_ajax_handler(get_unique_constraints))

AdvancedConnectionOpenAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced: Connection"])
)(create_ajax_handler(open_raw_connection))
AdvancedConnectionCloseAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced: Connection"])
)(create_ajax_handler(close_raw_connection))
AdvancedConnectionCommitAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced: Connection"])
)(create_ajax_handler(commit_raw_connection))
AdvancedConnectionRollbackAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced: Connection"])
)(create_ajax_handler(rollback_raw_connection))

AdvancedCursorOpenAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced: Cursor"])
)(create_ajax_handler(open_cursor))
AdvancedCursorCloseAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced: Cursor"])
)(create_ajax_handler(close_cursor))
AdvancedCursorFetchOneAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced: Cursor"])
)(create_ajax_handler(fetchone))

AdvancedSetIsolationLevelAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced"])
)(create_ajax_handler(set_isolation_level))
AdvancedGetIsolationLevelAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced"])
)(create_ajax_handler(get_isolation_level))
AdvancedDoBeginTwophaseAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced: Two phase"])
)(create_ajax_handler(do_begin_twophase))
AdvancedDoPrepareTwophaseAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced: Two phase"])
)(create_ajax_handler(do_prepare_twophase))
AdvancedDoRollbackTwophaseAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced: Two phase"])
)(create_ajax_handler(do_rollback_twophase))
AdvancedDoCommitTwophaseAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced: Two phase"])
)(create_ajax_handler(do_commit_twophase))
AdvancedDoRecoverTwophaseAPIView = extend_schema_view(
    post=extend_schema(tags=["Advanced: Two phase"])
)(create_ajax_handler(do_recover_twophase))
