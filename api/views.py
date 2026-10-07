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
from contextlib import contextmanager
from copy import deepcopy

import geoalchemy2  # noqa:F401 Although this import seems unused is has to be here
import requests
import zipstream
from django.conf import settings as django_settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Count, Q
from django.http import Http404, HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from drf_spectacular.views import SpectacularAPIView
from oemetadata.latest.example import OEMETADATA_LATEST_EXAMPLE
from oemetadata.latest.template import OEMETADATA_LATEST_TEMPLATE
from rest_framework import generics, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import (
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

import login.models as login_models
from api import bulk_upload_guard, sessions
from api.actions import (
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
from api.api_description import (
    ADVANCED_SESSION_NOTE,
    ALWAYS,
    DATASET_ANY_ACCOUNT,
    DATASET_CREATOR,
    DATASET_LIST_PUBLIC,
    DATASET_LIST_REFUSALS,
    DATASET_PAGE_NOT_FOUND,
    DATASET_PUBLIC,
    DELIMITER,
    IS_SANDBOX,
    OPENS_SESSION,
    OWNED_READ,
    OWNED_WRITE,
    PUBLIC_READ,
    PUBLIC_READ_WITH_FILTERS,
    QUERY_WRAPPER,
    ROW_FILTERS,
    TABLE,
    USES_POOL,
    AdvancedRequestSerializer,
    DatasetAssignedSerializer,
    DatasetUnassignedSerializer,
    QueryWrappedSerializer,
    RefusalSerializer,
    RowDeleteSerializer,
    RowSerializer,
    SparqlSerializer,
    TableAlterSerializer,
    TableCreateSerializer,
    dataset_responses,
    describes,
    responses,
)
from api.api_tags import (
    ADVANCED,
    ADVANCED_CONNECTION,
    ADVANCED_CURSOR,
    ADVANCED_TWO_PHASE,
    API_DESCRIPTION,
    DATASETS,
    FACTSHEETS,
    OEKG_SPARQL,
    SCENARIO_BUNDLES_LEGACY,
    TABLE_METADATA,
    TABLES,
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
    DatasetListFiltersSerializer,
    DatasetPatchSerializer,
    DatasetReadSerializer,
    DatasetResourceSerializer,
    DatasetSummarySerializer,
    EnergyframeworkSerializer,
    EnergymodelSerializer,
    ScenarioBundleScenarioDatasetSerializer,
    ScenarioDataTablesSerializer,
)
from api.services import dataset_actions, table_actions
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
from dataedit.models import DATASET_NOT_FOUND, BulkLoadEvent, Dataset, Table
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


@extend_schema(
    tags=[API_DESCRIPTION],
    summary="This description, as a document",
    description=(
        "The OpenAPI description of `api/v0`, generated from the code. It is "
        "what the reference page renders and what a generated client is built "
        "from.\n\nA copy is committed to the repository and a check keeps the "
        "two equal, so this endpoint and the published reference describe the "
        "same API."
    ),
)
class OpenAPIDescriptionAPIView(SpectacularAPIView):
    """The generated description, served by the platform.

    A subclass for one reason: the view is a third-party one and the group it
    belongs in is a decision of this project's. Annotating the imported class
    in place would set that on every project that imports it in this process.
    """


@extend_schema(tags=[TABLE_METADATA])
class TableMetadataAPIView(APIView):
    """
    Important note:
    oemetadata v2 introduces datasets which are not relevant on a table level
    always query for metadata["resources"][0]. Keeping the complete oemetadata v2 JSON
    makes it easy to integrate as no further changes to validation are required for now.
    Datasets are handled in the model.Datasets & api views.
    """

    @extend_schema(
        summary="Read a table's metadata",
        description=(
            "The table's OEMetadata document, as stored. A table carries one "
            "resource, so a reader wanting the table's own fields wants "
            "`resources[0]`."
        ),
        parameters=[TABLE],
        responses=responses({200: describes("The OEMetadata document.")}, *PUBLIC_READ),
    )
    @api_exception
    @method_decorator(never_cache)
    def get(self, request: Request, table: str) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)
        metadata = table_obj.get_metadata()
        return JsonResponse(metadata)

    @extend_schema(
        summary="Set a table's metadata",
        description=(
            "Replaces the stored OEMetadata document. The payload is the "
            "document itself, at the top level -- not wrapped in `query`. An "
            "older version is converted to the current one, the column list is "
            "synchronised with the table's actual columns, and the result is "
            "validated before anything is stored; a document that fails "
            "validation is refused and nothing changes. The table's keywords "
            "become its tags on this platform."
        ),
        parameters=[TABLE],
        request=OpenApiTypes.OBJECT,
        responses=responses({200: describes("The metadata as it was stored.")}),
    )
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


# What a write on a Dataset the user may read but did not create is told.
NOT_THE_CREATOR = "Only the dataset creator may modify this dataset."


@contextmanager
def answered_as_a_read():
    """Answer the Dataset action service's refusals of a Dataset as this
    API answers a read, so a write never tells more than a read: a Dataset
    the user may not read (a foreign draft, or no such name) is 404 in the
    words every read uses, one they may read but did not create 403, and an
    unusable parameter (the member ceiling among them) 400 in DRF's field
    map. Any other refusal passes through as the service raised it."""
    try:
        yield
    except dataset_actions.InvalidParameters as error:
        errors = {key: [message] for key, message in error.errors.items()}
        raise ValidationError(errors) from error
    except dataset_actions.DatasetNotFound as error:
        raise Http404(DATASET_NOT_FOUND) from error
    except dataset_actions.NotYourDataset as error:
        raise PermissionDenied(NOT_THE_CREATOR) from error
    except dataset_actions.ActionRefused as refused:
        if refused.not_found:
            raise Http404(DATASET_NOT_FOUND) from refused
        if refused.for_role:
            raise PermissionDenied(NOT_THE_CREATOR) from refused
        raise


def dataset_action(user, action, names, params):
    """Do ``action`` through the Dataset action service, the path the
    dashboard takes (spec #2613), with ``via="api"``."""
    with answered_as_a_read():
        return dataset_actions.execute(user, action, names, params, via="api")


def dataset_body(user, dataset_name) -> dict:
    """The read body of the Dataset ``dataset_name``, as ``user`` may read it:
    what a write answers with, so a client sees the state it left."""
    dataset = Dataset.objects.readable_or_404(user, dataset_name)
    return DatasetReadSerializer(dataset).data


def change_dataset_members(request, dataset_name, action):
    """The prologue both membership endpoints share: the table list
    validated, then the change made through the Dataset action service
    (``dataset_action``). Returns the table references sent and the
    ``Outcome``."""
    serializer = DatasetAssignTablesSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    refs = serializer.validated_data["tables"]
    names = [ref["name"] for ref in refs]
    outcome = dataset_action(request.user, action, names, {"dataset": dataset_name})
    return refs, outcome


DATASET_NAME = OpenApiParameter(
    name="dataset_name",
    location=OpenApiParameter.PATH,
    required=True,
    type=str,
    description=(
        "The dataset's name: its permanent identifier, fixed at creation. "
        "Names are global and are never reused."
    ),
)


class DatasetPagination(PageNumberPagination):
    """A ceiling, not a default: neither Dataset list has an unbounded mode.
    `page` and `page_size`, as every collection of the OEKG API pages. A
    class of its own rather than one of theirs, so a change to how an OEKG
    collection pages can not move this API's documented default."""

    page_size = 20
    page_size_query_param = "page_size"
    page_size_query_description = "How many per page: 20 if left out, at most 100."
    max_page_size = 100


# What `?mine=true` without a login is told.
MINE_NEEDS_A_LOGIN = "`mine=true` lists the caller's own datasets and needs a login."


@extend_schema(tags=[DATASETS])
@extend_schema_view(
    get=extend_schema(
        summary="List datasets",
        description=(
            "Every published dataset on the platform, plus the caller's own "
            "drafts, by name, a page at a time. `mine` and `published` narrow "
            "that and never widen it: `mine=true&published=false` lists the "
            "caller's drafts. Each item is a summary: the dataset's read body "
            "without `metadata.resources`, plus `resource_count`. The "
            "resources themselves are on the dataset's own read and its "
            "`resources/`. " + DATASET_LIST_PUBLIC
        ),
        parameters=[DatasetListFiltersSerializer],
        responses=dataset_responses(
            {200: DatasetSummarySerializer(many=True)},
            400,
            401,
            404,
            also=DATASET_LIST_REFUSALS,
        ),
    ),
    post=extend_schema(
        summary="Create a dataset",
        description=(
            "Creates a catalogue entry that tables can then be assigned to. "
            "The name must be free; a taken one is refused naming the field. "
            "`topics` must name existing topics, and never the draft "
            "pseudo-topic; a 400 names any that do not. " + DATASET_ANY_ACCOUNT
        ),
        request=DatasetCreateSerializer,
        responses=dataset_responses({201: DatasetReadSerializer}, 400, 401),
        examples=[
            OpenApiExample(
                "Dataset Example",
                summary="Example request body for creating a dataset",
                description=(
                    "Use this JSON object to create a new dataset. "
                    "The `at_id` field is optional and can contain "
                    "a persistent identifier; `topics` is optional too."
                ),
                value={
                    "name": "test_dataset",
                    "title": "Wind Power Dataset Germany",
                    "description": (
                        "Contains hourly wind generation data for Germany."
                    ),
                    "at_id": "https://example.org/datasets/test_dataset",
                    "topics": ["energy"],
                },
                request_only=True,
            )
        ],
    ),
)
class DatasetsListCreate(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = DatasetPagination

    def get_queryset(self):
        """What the caller may see (``visible_to``), narrowed by the filters.
        A page costs the same queries however many Datasets or members there
        are: the count, the page, the Topics."""
        filters = DatasetListFiltersSerializer(data=self.request.query_params)
        filters.is_valid(raise_exception=True)
        user = self.request.user
        if filters.only_mine and not user.is_authenticated:
            raise NotAuthenticated(MINE_NEEDS_A_LOGIN)
        return (
            filters.narrowed(Dataset.objects.visible_to(user), user)
            .select_related("creator")
            .prefetch_related("topics")
            .annotate(resource_count=Count("tables"))
            .order_by("name")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DatasetCreateSerializer
        return DatasetSummarySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        outcome = dataset_action(
            request.user, dataset_actions.CREATE, [data["name"]], data
        )
        return Response(
            DatasetReadSerializer(outcome.datasets[0]).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=[DATASETS])
@extend_schema_view(
    get=extend_schema(
        summary="List dataset resources",
        description=(
            "Returns the tables/resources that belong to a dataset, by name, "
            "a page at a time. " + DATASET_PUBLIC
        ),
        parameters=[DATASET_NAME],
        responses=dataset_responses(
            {200: DatasetResourceSerializer(many=True)},
            404,
            also=DATASET_PAGE_NOT_FOUND,
        ),
    )
)
class DatasetsListResources(generics.ListAPIView):
    serializer_class = DatasetResourceSerializer
    # declared, not inherited: REST_FRAMEWORK sets no default, and the draft
    # rule below is what keeps a draft's members private
    permission_classes = [AllowAny]
    pagination_class = DatasetPagination

    def get_queryset(self):
        dataset_name = self.kwargs["dataset_name"]
        dataset = Dataset.objects.readable_or_404(self.request.user, dataset_name)
        return dataset.tables.order_by("name")


@extend_schema(tags=[DATASETS])
@extend_schema_view(
    get=extend_schema(
        summary="Get dataset",
        description="Returns a single dataset with its metadata. " + DATASET_PUBLIC,
        parameters=[DATASET_NAME],
        responses=dataset_responses({200: DatasetReadSerializer}, 404),
    ),
    patch=extend_schema(
        summary="Update dataset",
        description=(
            "Changes the dataset's title, description, `at_id` or topics. A "
            "key left out is left as it is: `topics` replaces the whole set "
            "(`[]` empties it), and an omitted `at_id` keeps the stored one. "
            "`name` is fixed at creation, so sending it is a 400, even "
            "unchanged. Topics must exist and may not be the draft "
            "pseudo-topic; a 400 names any that do not. An update that "
            "changes nothing writes nothing and leaves `modified_at` as it "
            "was. Answers with the dataset as it now is. `PUT` is not "
            "offered and answers 405. " + DATASET_CREATOR
        ),
        parameters=[DATASET_NAME],
        request=DatasetPatchSerializer,
        responses=dataset_responses({200: DatasetReadSerializer}, 400, 401, 403, 404),
        examples=[
            OpenApiExample(
                "Update dataset example",
                summary="Change the title and replace the topics",
                value={
                    "title": "Updated Wind Power Dataset Germany",
                    "topics": ["energy"],
                },
                request_only=True,
            )
        ],
    ),
    delete=extend_schema(
        summary="Delete dataset",
        description=(
            "Deletes the dataset. Its member tables are not deleted; they "
            "only leave it. The address is the confirmation a published "
            "dataset asks for, and a repeated delete is a 404. " + DATASET_CREATOR
        ),
        parameters=[DATASET_NAME],
        responses=dataset_responses(
            {204: OpenApiResponse(description="Deleted. The body is empty.")},
            401,
            403,
            404,
        ),
    ),
)
class DatasetManager(APIView):
    """
    View to retrieve, update, or delete a single dataset's metadata.
    URL: /v0/datasets/<dataset_name>/
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, dataset_name):
        dataset = Dataset.objects.readable_or_404(request.user, dataset_name)
        serializer = DatasetReadSerializer(dataset)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, dataset_name):
        serializer = DatasetPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dataset_action(
            request.user,
            dataset_actions.EDIT,
            [dataset_name],
            serializer.validated_data,
        )
        return Response(dataset_body(request.user, dataset_name))

    def delete(self, request, dataset_name):
        # the address is the typed confirmation a published Dataset asks for
        dataset_action(
            request.user,
            dataset_actions.DELETE,
            [dataset_name],
            {"confirm": dataset_name},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class DatasetTransition(APIView):
    """Publish or unpublish one Dataset (``transition``) through the Dataset
    action service. No body is read. Answers 200 with the Dataset as it now
    is, also when nothing had to change (unpublishing a draft)."""

    permission_classes = [IsAuthenticated]
    transition = None

    def post(self, request, dataset_name):
        try:
            dataset_action(request.user, self.transition, [dataset_name], {})
        except dataset_actions.ActionRefused as refused:
            # a Dataset not there or not the user's has been answered as a
            # read already (``answered_as_a_read``): what is left is the
            # Dataset's own state, the publish gate, which only a publish
            # can fail
            if not refused.failed_checks:
                raise
            reasons = "; ".join(group.reason for group in refused.refused)
            return Response(
                {
                    "detail": (
                        "Not published: the dataset does not pass the publish "
                        f"gate ({reasons}). Nothing was changed."
                    ),
                    "failed": refused.failed_checks,
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(dataset_body(request.user, dataset_name))


@extend_schema(tags=[DATASETS])
@extend_schema_view(
    post=extend_schema(
        summary="Publish a dataset",
        description=(
            "Publishes the dataset: it enters the catalogue and anyone may "
            "read it. The publish gate runs now and needs at least one member "
            "table and at least one topic; a dataset failing it is a 409 "
            "listing the failed checks in `failed`, and nothing is written. "
            "Members may be drafts or under embargo. Publishing a published "
            "dataset republishes it: the gate runs again and `published_at` "
            "becomes now. Never moves `modified_at`. No request body. "
            + DATASET_CREATOR
        ),
        parameters=[DATASET_NAME],
        request=None,
        responses=dataset_responses({200: DatasetReadSerializer}, 401, 403, 404, 409),
    )
)
class DatasetPublish(DatasetTransition):
    transition = dataset_actions.PUBLISH


@extend_schema(tags=[DATASETS])
@extend_schema_view(
    post=extend_schema(
        summary="Unpublish a dataset",
        description=(
            "Returns the dataset to draft: it leaves the catalogue, other "
            "users get 404 for it, and scenario citations of it stop "
            "resolving. Always allowed for the creator; unpublishing a draft "
            "succeeds and writes nothing. Never moves `modified_at`. No "
            "request body. " + DATASET_CREATOR
        ),
        parameters=[DATASET_NAME],
        request=None,
        responses=dataset_responses({200: DatasetReadSerializer}, 401, 403, 404),
    )
)
class DatasetUnpublish(DatasetTransition):
    transition = dataset_actions.UNPUBLISH


@extend_schema(tags=[DATASETS])
class AssignDatasetTables(APIView):
    """
    Assign existing OEP tables to an existing dataset.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Assign tables to dataset",
        description=(
            "Assigns existing OEP tables to an existing dataset; the tables' "
            "topics are added to the dataset's. Any published table not under "
            "embargo may be assigned; a draft or embargoed table needs Data "
            "editor on it, and one that does not qualify refuses the whole "
            "request. A name that is no table is reported in `missing` rather "
            "than refused. At most 2,500 tables in one call. " + DATASET_CREATOR
        ),
        parameters=[DATASET_NAME],
        request=DatasetAssignTablesSerializer,
        responses=dataset_responses(
            {200: DatasetAssignedSerializer},
            401,
            404,
            also={
                400: describes(
                    "The table list is unusable, or names more than 2,500: "
                    "DRF's map of each field to what is wrong with it."
                ),
                403: OpenApiResponse(
                    response=RefusalSerializer,
                    description=(
                        "Authenticated, but the dataset is somebody else's, or "
                        "a table named is a draft or under embargo and the "
                        "account holds no Data editor on it. Nothing was "
                        "assigned."
                    ),
                ),
            },
        ),
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
        try:
            refs, outcome = change_dataset_members(
                request, dataset_name, dataset_actions.MEMBERS_ADD
            )
        except dataset_actions.ActionRefused as refused:
            forbidden = [name for group in refused.refused for name in group.names]
            raise PermissionDenied(
                "Draft or embargoed tables require Data editor on the table, "
                "directly or through an organization, to be assigned: "
                f"{', '.join(forbidden)}."
            ) from refused

        missing = {
            name
            for group in outcome.left_out
            if group.reason == dataset_actions.NO_SUCH_TABLE
            for name in group.names
        }
        # A Table the Dataset holds already is reported as added, as it
        # always was: after the call it is in the Dataset, so a repeated
        # call answers as the first did.
        added_tables = [ref["name"] for ref in refs if ref["name"] not in missing]
        return Response(
            {
                "message": f"Added {len(added_tables)} tables.",
                "added": added_tables,
                "missing": [ref for ref in refs if ref["name"] in missing],
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=[DATASETS])
class UnassignDatasetTables(APIView):
    """Detach tables from a dataset. The tables themselves are untouched."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Unassign tables from a dataset",
        description=(
            "Removes the named tables from the dataset. The tables are not "
            "deleted -- a dataset is a catalogue entry, and leaving it is not "
            "leaving the platform. A name the dataset does not hold is "
            "reported in `missing` rather than refused, so a repeated call is "
            "safe. The dataset's topics stay as they are. At most 2,500 "
            "tables in one call. " + DATASET_CREATOR
        ),
        parameters=[DATASET_NAME],
        request=DatasetAssignTablesSerializer,
        responses=dataset_responses(
            {200: DatasetUnassignedSerializer},
            401,
            403,
            404,
            also={
                400: describes(
                    "The table list is unusable, or names more than 2,500: "
                    "DRF's map of each field to what is wrong with it."
                )
            },
        ),
    )
    def post(self, request, dataset_name):
        refs, outcome = change_dataset_members(
            request, dataset_name, dataset_actions.MEMBERS_REMOVE
        )
        removed = {table.name for table in outcome.tables}
        removed_tables = [ref["name"] for ref in refs if ref["name"] in removed]
        missing = [ref for ref in refs if ref["name"] not in removed]

        return Response(
            {
                "message": f"Removed {len(removed_tables)} tables.",
                "removed": removed_tables,
                "missing": missing,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=[TABLES])
class TableAPIView(APIView):
    """
    Handles the creation of tables and serves information on existing tables
    """

    objects = None

    @extend_schema(
        summary="Describe a table",
        description=(
            "The table's structure: its columns, its indexes and its "
            "constraints. Not its rows -- those are at `rows/`."
        ),
        parameters=[TABLE],
        responses=responses(
            {
                200: describes(
                    "`name`, `columns`, `indexed` and `constraints`, each "
                    "keyed by name."
                )
            },
            *PUBLIC_READ,
        ),
    )
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

    @extend_schema(
        summary="Change a table's columns or constraints",
        description=(
            "Queues a change to an existing table's structure. It is not "
            "applied on the spot: it lands in the change-request queue for "
            "review.\n\n"
            "**The payload is at the top level here**, unlike the `PUT` on "
            "this same address, which reads it out of `query`. `type` decides "
            "which kind of change is meant; anything else is refused."
        ),
        parameters=[TABLE],
        request=TableAlterSerializer,
        responses=responses(
            {200: describes("What the queued change came to.")}, *OWNED_WRITE
        ),
    )
    @api_exception
    @require_write_permission
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

    @extend_schema(
        summary="Create a table",
        description=(
            "Creates the table and its metadata row. **Two things about this "
            "endpoint catch people out.** The target schema comes from the "
            "`is_sandbox` query parameter, not from the payload. And table "
            "names are global -- a name already taken anywhere on the "
            "platform is a `409`, whichever schema or topic holds it.\n\n"
            + QUERY_WRAPPER
        ),
        parameters=[TABLE, IS_SANDBOX],
        request=TableCreateSerializer,
        responses=responses(
            {201: describes("Created. The body is empty; the table is at this URL.")},
            400,
            401,
            409,
        ),
    )
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

    @extend_schema(
        summary="Delete a table",
        description=(
            "Removes the table and its metadata. Irreversible, and it takes "
            "the rows with it."
        ),
        parameters=[TABLE],
        responses=responses(
            {200: describes("Deleted. The body is empty.")}, 401, 403, 404
        ),
    )
    @api_exception
    @require_delete_permission
    def delete(self, request: Request, table: str) -> JsonLikeResponse:
        # The address names the Table, which is all the dashboard's typed
        # confirmation asks for. Whether the API should guard deleting a
        # published Table is a platform rule outside spec #2551.
        outcome = table_action(
            request.user, table_actions.DELETE, table, {"confirm": table}
        )
        if outcome and outcome.drop_failed:
            # The record is gone (a retry is a 404), its data is not.
            return JsonResponse(
                {
                    "reason": f"The table {table} was deleted, but its data "
                    "could not be removed from the database. This is logged; "
                    "please tell the platform's operators."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return JsonResponse({}, status=status.HTTP_200_OK)


@extend_schema(tags=[TABLES])
class TableColumnAPIView(APIView):
    @extend_schema(
        summary="Describe a column, or every column",
        description=(
            "One column's definition, or the whole set when the address ends "
            "at `columns/`."
        ),
        parameters=[
            TABLE,
            OpenApiParameter(
                name="column",
                location=OpenApiParameter.PATH,
                required=False,
                type=str,
                description="The column's name. Omit it for every column.",
            ),
        ],
        responses=responses(
            {200: describes("The column definitions, keyed by name.")},
            *PUBLIC_READ_WITH_FILTERS,
        ),
    )
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

    @extend_schema(
        summary="Alter a column",
        description="Changes an existing column's definition.\n\n" + QUERY_WRAPPER,
        parameters=[
            TABLE,
            OpenApiParameter(
                name="column",
                location=OpenApiParameter.PATH,
                required=True,
                type=str,
                description="The column's name.",
            ),
        ],
        request=QueryWrappedSerializer,
        responses=responses({200: describes("What the change came to.")}),
    )
    @api_exception
    @require_write_permission
    def post(self, request: Request, table: str, column: str) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)

        request_data_dict = get_request_data_dict(request)
        response = column_alter(request_data_dict["query"], table_obj, column)
        return JsonResponse(response)

    @extend_schema(
        summary="Add a column",
        description="Adds a column to an existing table.\n\n" + QUERY_WRAPPER,
        parameters=[
            TABLE,
            OpenApiParameter(
                name="column",
                location=OpenApiParameter.PATH,
                required=True,
                type=str,
                description="The column's name.",
            ),
        ],
        request=QueryWrappedSerializer,
        responses=responses({201: describes("Added. The body is empty.")}),
    )
    @api_exception
    @require_write_permission
    def put(self, request: Request, table: str, column: str) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)
        request_data_dict = get_request_data_dict(request)
        column_add(table_obj, column, request_data_dict["query"])
        return JsonResponse({}, status=201)


_ROLE_REFUSALS = frozenset(gate.refusal for gate in table_actions.ROLE_GATES.values())


def table_action(user, action, table, params=None, holds_already=None):
    """Do ``action`` on the one Table ``table`` through the table action
    service, the path the dashboard takes (spec #2551), and answer its
    refusals as this API answers the same situations elsewhere.

    The permission decorators have checked the Table and the role already;
    the service checks both again under a row lock, so a refusal there means
    something changed in between: a Table gone is a 404, a role gone a 403
    (the service says "Not one of your tables" for both, and the API tells
    them apart, as its decorators do). Anything else the service refuses,
    and every unusable parameter, is a 400 naming why. ``holds_already`` is
    a refusal that means the request's outcome holds already: it answers
    success, with nothing written, and returns None.

    Never called inside a transaction: a delete's is durable, and the
    service refuses to run it nested. ``ATOMIC_REQUESTS`` is off.
    """
    try:
        return table_actions.execute(user, action, [table], params, via="api")
    except table_actions.InvalidParameters as error:
        raise APIError(str(error), 400) from error
    except table_actions.ActionRefused as refused:
        reasons = {group.reason for group in refused.refused}
        if reasons == {holds_already}:
            return None
        if table_actions.NOT_YOURS in reasons:
            if not Table.objects.filter(name=table).exists():
                raise APIError("Table does not exist", 404) from refused
            raise APIError("Permission denied", 403) from refused
        if reasons & _ROLE_REFUSALS:
            raise APIError("Permission denied", 403) from refused
        raise APIError(refused.message, 400) from refused


@extend_schema(tags=[TABLES])
class TableMovePublishAPIView(APIView):
    @extend_schema(
        summary="Publish a table under a topic",
        description=(
            "Moves the table into a topic and marks it published. Needs "
            "administrator permission on the table. An embargo may be given "
            "either at the top level or inside `query` -- this endpoint reads "
            "both, which is worth knowing because its neighbours do not."
        ),
        parameters=[
            TABLE,
            OpenApiParameter(
                name="topic",
                location=OpenApiParameter.PATH,
                required=True,
                type=str,
                description="The topic to publish under.",
            ),
        ],
        request=OpenApiTypes.OBJECT,
        responses=responses({200: describes("Published. The body is empty.")}),
    )
    @api_exception
    @require_admin_permission
    def post(self, request: Request, table: str, topic: str) -> JsonLikeResponse:
        # Make payload more friendly as users tend to use the query wrapper in payload
        request_data_dict = get_request_data_dict(request)
        payload_query = request_data_dict.get("query", {})
        embargo_period = request_data_dict.get("embargo", {}).get(
            "duration", None
        ) or payload_query.get("embargo", {}).get("duration", None)
        # A published Table is published again (one more Topic, the embargo
        # given), and an omitted embargo leaves it as it is: what this
        # endpoint has always done, unlike the dashboard's publish.
        table_action(
            request.user,
            table_actions.PUBLISH,
            table,
            {
                "topic": topic,
                "embargo": embargo_period or table_actions.KEEP_EMBARGO,
                "republish": True,
            },
        )
        return JsonResponse({}, status=status.HTTP_200_OK)


@extend_schema(tags=[TABLES])
class TableUnpublishAPIView(APIView):
    @extend_schema(
        summary="Unpublish a table",
        description=(
            "Marks the table not published. It keeps its topic and its rows; "
            "what changes is whether it is listed. Needs administrator "
            "permission on the table."
        ),
        parameters=[TABLE],
        request=None,
        responses=responses(
            {200: describes("Unpublished. The body is empty.")}, 401, 403, 404
        ),
    )
    @api_exception
    @require_admin_permission
    def post(self, request: HttpRequest, table: str) -> JsonLikeResponse:
        """Set table to `not published`"""
        # a draft is unpublished already: success, as it has always been
        table_action(
            request.user,
            table_actions.UNPUBLISH,
            table,
            holds_already=table_actions.NOT_PUBLISHED,
        )
        return JsonResponse({}, status=status.HTTP_200_OK)


@extend_schema(tags=[TABLES])
class TableRowsAPIView(APIView):
    @extend_schema(
        summary="Read rows",
        description=(
            "One row by id, or the rows a filter selects. The filter "
            "parameters and a row id are mutually exclusive: an id already "
            "names one row, so sending both is refused rather than silently "
            "resolved one way."
        ),
        parameters=[
            TABLE,
            OpenApiParameter(
                name="row_id",
                location=OpenApiParameter.PATH,
                required=False,
                type=int,
                description=(
                    "One row's id. Omit it to address the whole table; the "
                    "filter parameters are then what select rows."
                ),
            ),
            *ROW_FILTERS,
        ],
        responses=responses(
            {200: describes("The rows, as a list of objects keyed by column name.")},
            *OWNED_READ,
        ),
    )
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

    @extend_schema(
        summary="Insert or update rows",
        description=(
            "At `rows/new` this inserts and answers `201`. At `rows/<id>` it "
            "updates that row, and at `rows/` it updates the rows a filter "
            "selects.\n\n" + QUERY_WRAPPER
        ),
        parameters=[
            TABLE,
            OpenApiParameter(
                name="row_id",
                location=OpenApiParameter.PATH,
                required=False,
                type=int,
                description=(
                    "One row's id. Omit it to address the whole table; the "
                    "filter parameters are then what select rows."
                ),
            ),
        ],
        request=RowSerializer,
        responses=responses(
            {
                200: describes("The rows as they now stand."),
                201: describes("Inserted."),
            }
        ),
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
        return stream(response, status_code=status_code)

    @extend_schema(
        summary="Put one row at an id",
        description=(
            "Updates the row at this id, or inserts it there if it is not yet "
            "taken. **An id never changes**: an `id` in the payload that "
            "disagrees with the one in the address is a `409` rather than a "
            "move. Requires an id -- `rows/new` is a `POST`.\n\n" + QUERY_WRAPPER
        ),
        parameters=[
            TABLE,
            OpenApiParameter(
                name="row_id",
                location=OpenApiParameter.PATH,
                required=True,
                type=int,
                description="The row's id.",
            ),
        ],
        request=RowSerializer,
        responses=responses(
            {
                200: describes("Updated."),
                201: describes("Inserted at that id."),
            },
            *ALWAYS,
            409,
        ),
    )
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
            return JsonResponse(response)
        else:
            result = self.__insert_row(request, table_obj, payload_query, row_id)
            return JsonResponse(result, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Delete rows",
        description=(
            "One row by id, or the rows a `where` filter selects. Deleting "
            "with neither deletes every row in the table."
        ),
        parameters=[
            TABLE,
            OpenApiParameter(
                name="row_id",
                location=OpenApiParameter.PATH,
                required=False,
                type=int,
                description=(
                    "One row's id. Omit it to address the whole table; the "
                    "filter parameters are then what select rows."
                ),
            ),
            *ROW_FILTERS,
        ],
        request=RowDeleteSerializer,
        responses=responses({200: describes("What was deleted.")}, *OWNED_WRITE),
    )
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


@extend_schema(tags=[TABLES])
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

    @extend_schema(
        summary="Append a CSV to a table",
        description=(
            "**The request body is the CSV itself**, not JSON wrapping one. "
            "Rows are appended in one transaction: either the whole upload "
            "lands or none of it does. It bypasses the edit journal, so there "
            "is no per-row history for what it writes -- the `BulkLoadEvent` "
            "it leaves is the upload's provenance.\n\n"
            "Send it gzipped (`Content-Encoding: gzip`) unless the file is "
            "small: the platform is not the bottleneck on a large upload, the "
            "client's uplink is, and CSV compresses well enough to change what "
            "is reachable.\n\n"
            "At most one upload per account runs at a time; a second answers "
            "`429` with `Retry-After` and writes nothing."
        ),
        parameters=[TABLE, DELIMITER],
        request={"text/csv": OpenApiTypes.STR},
        responses=responses(
            {
                201: describes(
                    "Appended. `rows` is how many, `id_range` the first and "
                    "last id written, and `event_id` names the BulkLoadEvent "
                    "this upload left."
                )
            },
            *ALWAYS,
            also={
                429: describes(
                    "Another upload of yours is already running, or the "
                    "platform is at its limit. Nothing was written and no "
                    "event recorded. `Retry-After` says how long to wait."
                )
            },
        ),
    )
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

        table_obj.stamp_data_modified()
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
def groupprop_api_view(request: Request) -> JsonLikeResponse:
    """
    Return all groups where this user is a member that match
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
    similar_organizations = (
        login_models.Organization.objects.annotate(
            similarity=TrigramSimilarity("name", query),
        )
        .filter(
            similarity__gt=0.2,  # Adjust the threshold as needed
            id__in=[organization.pk for organization in groups],
        )
        .order_by("-similarity")[:5]
    )

    group_names = [group.name for group in similar_organizations]

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


@extend_schema(tags=[OEKG_SPARQL])
class OekgSparqlAPIView(APIView):
    """A read-only SPARQL endpoint over the OEKG."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Query the OEKG with SPARQL",
        description=(
            "Hands a query to the graph store and returns what comes back. "
            "**Reads only**: a query that would update or delete is refused "
            "whatever the caller's permissions, so this is not a way to write "
            "to the graph. The scenario-bundle endpoints are, and they "
            "validate what they write against the OEKG shape.\n\n"
            "Authenticated by token. A `format` other than `json` is returned "
            "with the store's own content type rather than parsed."
        ),
        request=SparqlSerializer,
        responses=responses(
            {200: describes("The store's answer, in the format asked for.")},
            400,
            401,
        ),
    )
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
@extend_schema(tags=[FACTSHEETS])
@method_decorator(never_cache, name="dispatch")
class EnergyframeworkFactsheetListAPIView(generics.ListAPIView):
    """
    Used for the scenario bundles react app to be able to select a existing
    framework or model factsheet.
    """

    queryset = Energyframework.objects.all()
    serializer_class = EnergyframeworkSerializer


@extend_schema(tags=[FACTSHEETS])
@method_decorator(never_cache, name="dispatch")
class EnergymodelFactsheetListAPIView(generics.ListAPIView):
    """
    Used for the scenario bundles react app to be able to select a existing
    framework or model factsheet.
    """

    queryset = Energymodel.objects.all()
    serializer_class = EnergymodelSerializer


@extend_schema(tags=[TABLES])
@method_decorator(never_cache, name="dispatch")
class ScenarioDataTablesListAPIView(generics.ListAPIView):
    """
    Used for the scenario bundles react app to be able to populate
    form select options with existing datasets from scenario topic.
    """

    queryset = Table.objects.filter(topics__name=TOPIC_SCENARIO)
    serializer_class = ScenarioDataTablesSerializer


@extend_schema(tags=[SCENARIO_BUNDLES_LEGACY])
class ManageOekgScenarioDatasetsAPIView(APIView):
    """The token-authenticated HTTP route for attaching datasets to a scenario.

    Built for scripts (#1890), not for the user interface, which has never
    called it: the scenario-bundle editor writes through
    `scenario-bundles/update/`.
    """

    permission_classes = [IsAuthenticated]  # Require authentication

    @extend_schema(
        summary="Attach datasets to a scenario (superseded)",
        description=(
            "**Superseded** by the scenario-bundle dataset-link endpoints "
            "under `/api/v0/scenario-bundles/<uid>/scenarios/<sid>/datasets/`, "
            "which validate what they write against the OEKG shape and say on "
            "every read whether a citation still resolves. This route writes "
            "predicates the canonical shape does not validate; it is kept "
            "for scripts written against it before that API existed."
        ),
        request=ScenarioBundleScenarioDatasetSerializer,
        responses=responses(
            {200: describes("What was attached.")},
            400,
            401,
            403,
        ),
    )
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


@extend_schema(tags=[TABLES])
class AllTableSizesAPIView(APIView):
    """
    GET /api/v0/db/table-sizes/?stopic=<stopic>&table=<table>
    - table -> single relation (detailed)
    - none  -> all tables
    """

    @extend_schema(
        summary="Table sizes",
        description=(
            "How much space tables take in the database. Without `table` this "
            "lists every table; with one it describes that table in detail."
        ),
        parameters=[
            OpenApiParameter(
                name="table",
                location=OpenApiParameter.QUERY,
                required=False,
                type=str,
                description="One table's name. Omit it for the whole list.",
            )
        ],
        responses=responses({200: describes("The sizes.")}, *PUBLIC_READ),
    )
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


@extend_schema_view(
    post=extend_schema(
        tags=[ADVANCED_CURSOR],
        summary="Fetch rows from an open cursor",
        description=(
            "Streams rows from a cursor opened by `advanced/cursor/open`, one "
            "JSON array per line rather than one document -- so a large result "
            "can be read without holding it whole.\n\n" + ADVANCED_SESSION_NOTE
        ),
        request=AdvancedRequestSerializer,
        responses=responses(
            {
                200: describes(
                    "One row per line, each a JSON array of cell values in "
                    "column order."
                )
            },
            400,
            403,
        ),
    )
)
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


@extend_schema_view(
    get=extend_schema(
        tags=[ADVANCED_CONNECTION],
        summary="Close every connection this account holds",
        description=(
            "Closes all of this account's open database connections. The way "
            "out of a session left open by a client that stopped without "
            "closing it.\n\n" + ADVANCED_SESSION_NOTE
        ),
        responses=responses({200: describes("Closed.")}, 403),
    )
)
class AdvancedCloseAllAPIView(LoginRequiredMixin, APIView):
    @api_exception
    def get(self, request: Request) -> JsonLikeResponse:
        sessions.close_all_for_user(request.user)
        return JsonResponse({"message": "All connections closed"})


AdvancedSearchAPIView = extend_schema_view(post=extend_schema(tags=[ADVANCED]))(
    create_ajax_handler(
        data_search, allow_cors=True, requires_cursor=True, refusals=OPENS_SESSION
    )
)
AdvancedInsertAPIView = extend_schema_view(post=extend_schema(tags=[ADVANCED]))(
    create_ajax_handler(data_insert, requires_cursor=True, refusals=OPENS_SESSION)
)
AdvancedDeleteAPIView = extend_schema_view(post=extend_schema(tags=[ADVANCED]))(
    create_ajax_handler(data_delete, requires_cursor=True, refusals=OPENS_SESSION)
)
AdvancedUpdateAPIView = extend_schema_view(post=extend_schema(tags=[ADVANCED]))(
    create_ajax_handler(data_update, requires_cursor=True, refusals=OPENS_SESSION)
)


AdvancedHasSchemaAPIView = extend_schema_view(post=extend_schema(tags=[ADVANCED]))(
    create_ajax_handler(has_schema)
)
AdvancedHasTableAPIView = extend_schema_view(post=extend_schema(tags=[ADVANCED]))(
    create_ajax_handler(has_table)
)
AdvancedGetSchemaNamesAPIView = extend_schema_view(post=extend_schema(tags=[ADVANCED]))(
    create_ajax_handler(get_schema_names)
)
AdvancedGetTableNamesAPIView = extend_schema_view(post=extend_schema(tags=[ADVANCED]))(
    create_ajax_handler(get_table_names)
)
AdvancedGetViewNamesAPIView = extend_schema_view(post=extend_schema(tags=[ADVANCED]))(
    create_ajax_handler(get_view_names)
)
AdvancedGetViewDefinitionAPIView = extend_schema_view(
    post=extend_schema(tags=[ADVANCED])
)(create_ajax_handler(get_view_definition))
AdvancedGetColumnsAPIView = extend_schema_view(post=extend_schema(tags=[ADVANCED]))(
    create_ajax_handler(get_columns, refusals=USES_POOL)
)
AdvancedGetPkConstraintAPIView = extend_schema_view(
    post=extend_schema(tags=[ADVANCED])
)(create_ajax_handler(get_pk_constraint, refusals=USES_POOL))
AdvancedGetForeignKeysAPIView = extend_schema_view(post=extend_schema(tags=[ADVANCED]))(
    create_ajax_handler(get_foreign_keys, refusals=USES_POOL)
)
AdvancedGetIndexesAPIView = extend_schema_view(post=extend_schema(tags=[ADVANCED]))(
    create_ajax_handler(get_indexes, refusals=USES_POOL)
)
AdvancedGetUniqueConstraintsAPIView = extend_schema_view(
    post=extend_schema(tags=[ADVANCED])
)(create_ajax_handler(get_unique_constraints, refusals=USES_POOL))

AdvancedConnectionOpenAPIView = extend_schema_view(
    post=extend_schema(tags=[ADVANCED_CONNECTION])
)(create_ajax_handler(open_raw_connection, refusals=OPENS_SESSION))
AdvancedConnectionCloseAPIView = extend_schema_view(
    post=extend_schema(tags=[ADVANCED_CONNECTION])
)(create_ajax_handler(close_raw_connection, refusals=OPENS_SESSION))
AdvancedConnectionCommitAPIView = extend_schema_view(
    post=extend_schema(tags=[ADVANCED_CONNECTION])
)(create_ajax_handler(commit_raw_connection, refusals=OPENS_SESSION))
AdvancedConnectionRollbackAPIView = extend_schema_view(
    post=extend_schema(tags=[ADVANCED_CONNECTION])
)(create_ajax_handler(rollback_raw_connection, refusals=OPENS_SESSION))

AdvancedCursorOpenAPIView = extend_schema_view(
    post=extend_schema(tags=[ADVANCED_CURSOR])
)(create_ajax_handler(open_cursor, refusals=OPENS_SESSION))
AdvancedCursorCloseAPIView = extend_schema_view(
    post=extend_schema(tags=[ADVANCED_CURSOR])
)(create_ajax_handler(close_cursor, refusals=OPENS_SESSION))
AdvancedCursorFetchOneAPIView = extend_schema_view(
    post=extend_schema(tags=[ADVANCED_CURSOR])
)(create_ajax_handler(fetchone, refusals=OPENS_SESSION))

AdvancedSetIsolationLevelAPIView = extend_schema_view(
    post=extend_schema(tags=[ADVANCED])
)(create_ajax_handler(set_isolation_level, refusals=OPENS_SESSION))
AdvancedGetIsolationLevelAPIView = extend_schema_view(
    post=extend_schema(tags=[ADVANCED])
)(create_ajax_handler(get_isolation_level, refusals=OPENS_SESSION))
AdvancedDoBeginTwophaseAPIView = extend_schema_view(
    post=extend_schema(tags=[ADVANCED_TWO_PHASE])
)(create_ajax_handler(do_begin_twophase, refusals=OPENS_SESSION))
AdvancedDoPrepareTwophaseAPIView = extend_schema_view(
    post=extend_schema(tags=[ADVANCED_TWO_PHASE])
)(create_ajax_handler(do_prepare_twophase, refusals=OPENS_SESSION))
AdvancedDoRollbackTwophaseAPIView = extend_schema_view(
    post=extend_schema(tags=[ADVANCED_TWO_PHASE])
)(create_ajax_handler(do_rollback_twophase, refusals=OPENS_SESSION))
AdvancedDoCommitTwophaseAPIView = extend_schema_view(
    post=extend_schema(tags=[ADVANCED_TWO_PHASE])
)(create_ajax_handler(do_commit_twophase, refusals=OPENS_SESSION))
AdvancedDoRecoverTwophaseAPIView = extend_schema_view(
    post=extend_schema(tags=[ADVANCED_TWO_PHASE])
)(create_ajax_handler(do_recover_twophase, refusals=OPENS_SESSION))
