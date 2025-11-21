"""This is the initial view that initialises the database connection.

SPDX-FileCopyrightText: 2025 Pierre Francois <https://github.com/Bachibouzouk> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Pierre Francois <https://github.com/Bachibouzouk> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Eike Broda <https://github.com/ebroda>
SPDX-FileCopyrightText: 2025 Hendrik Huyskens <https://github.com/henhuy> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>  © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>  © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Kirann Bhavaraju <https://github.com/KirannBhavaraju> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Ludwig Hülk <https://github.com/Ludee> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Ludwig Hülk <https://github.com/Ludee> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Tom Heimbrodt <https://github.com/tom-heimbrodt>
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Christian Hofmann <https://github.com/christian-rli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 shara <https://github.com/SharanyaMohan-30> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Stephan Uller <https://github.com/steull> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 user <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import csv
import json
import re
from collections import defaultdict
from io import TextIOWrapper
from itertools import chain

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, F
from django.db.utils import IntegrityError
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.generic import View
from oemetadata.v2.v20.schema import OEMETADATA_V20_SCHEMA

import login.permissions
from api.actions import (
    apply_queued_column,
    apply_queued_constraint,
    assert_add_tag_permission,
    data_insert,
    describe_columns,
    get_or_403,
    perform_sql,
    remove_queued_column,
    remove_queued_constraint,
    table_or_404,
)
from api.error import APIError
from dataedit.forms import GeomViewForm, GraphViewForm, LatLonViewForm
from dataedit.helper import (
    TODO_PSEUDO_TOPIC_DRAFT,
    add_tag,
    change_requests,
    delete_peer_review,
    delete_tag,
    edit_tag,
    find_tables,
    get_cancle_state,
    get_column_description,
    get_page,
    merge_field_reviews,
    process_review_data,
    recursive_update,
    send_dump,
    update_keywords_from_tags,
)
from dataedit.metadata import load_metadata_from_db, save_metadata_to_db
from dataedit.metadata.widget import MetaDataWidget
from dataedit.models import (
    Embargo,
)
from dataedit.models import Filter as DBFilter
from dataedit.models import (
    PeerReview,
    PeerReviewManager,
    Table,
    TableRevision,
    Tag,
    Topic,
)
from dataedit.models import View as DBView
from dataedit.models import View as DataViewModel
from login import models as login_models
from oeplatform.settings import DOCUMENTATION_LINKS, EXTERNAL_URLS, SCHEMA_DATA

ITEMS_PER_PAGE = 50  # how many tabled per page should be displayed


class StandaloneMetaEditView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        context_dict = {
            "config": json.dumps(
                {"cancle_url": get_cancle_state(self.request), "standalone": True}
            ),
            "oem_key_desc": EXTERNAL_URLS["oemetadata_key_description"],
            "oemetadata_tutorial": EXTERNAL_URLS["tutorials_oemetadata"],
            "oemetabuilder_tutorial": EXTERNAL_URLS["tutorials_oemetabuilder"],
        }
        return render(
            request,
            "dataedit/meta_edit.html",
            context=context_dict,
        )


@require_POST
def admin_constraints_view(request: HttpRequest) -> HttpResponse:
    """
    Way to apply changes
    :param request:
    :return:
    """
    action = request.POST.get("action")
    id = request.POST.get("id")
    schema = request.POST.get("schema")
    table = request.POST.get("table")

    if action == "deny":
        remove_queued_constraint(id)
    elif action == "apply":
        apply_queued_constraint(id)
    else:
        raise NotImplementedError(action)

    return redirect("dataedit:view", schema=schema, table=table)


@require_POST
def admin_column_view(request: HttpRequest) -> HttpResponse:
    """
    Way to apply changes
    :param request:
    :return:
    """

    action = request.POST.get("action")
    id = request.POST.get("id")
    schema = request.POST.get("schema")
    table = request.POST.get("table")

    if action == "deny":
        remove_queued_column(id)
    elif action == "apply":
        apply_queued_column(id)
    else:
        raise NotImplementedError(action)

    return redirect("dataedit:view", schema=schema, table=table)


def topic_view(request: HttpRequest) -> HttpResponse:
    """
    Loads all schemas that are present in the external database specified in
    oeplatform/securitysettings.py. Only schemas that are present in the
    whitelist are processed that do not start with an underscore.

    :param request: A HTTP-request object sent by the Django framework

    :return: Renders the schema list
    """

    searched_query_string = request.GET.get("query")
    searched_tag_ids = request.GET.getlist("tags")

    Tag.increment_usage_count_many(searched_tag_ids)

    # find all tables (layzy query set)
    tables = find_tables(query_string=searched_query_string, tag_ids=searched_tag_ids)

    description = {
        "boundaries": "Data that depicts boundaries, such as geographic, administrative or political boundaries. Such data comes as polygons.",  # noqa
        "climate": "Data related to climate and weather. This includes, for example, precipitation, temperature, cloud cover and atmospheric conditions.",  # noqa
        "economy": "Data related to economic activities. Examples: sectoral value added, sectoral inputs and outputs, GDP, prices of commodities etc.",  # noqa
        "demand": "Data on demand. Demand can relate to commodities but also to services.",  # noqa
        "grid": "Energy transmission infrastructure. examples: power lines, substation, pipelines",  # noqa
        "supply": "Data on supply. Supply can relate to commodities but also to services.",  # noqa
        "environment": "environmental resources, protection and conservation. examples: environmental pollution, waste storage and treatment, environmental impact assessment, monitoring environmental risk, nature reserves, landscape",  # noqa
        "society": "Demographic data such as population statistics and projections, fertility, mortality etc.",  # noqa
        "model_draft": "Unfinished data of any kind. Note: there is no version control and data is still volatile.",  # noqa
        "scenario": "Scenario data in the broadest sense. Includes input and output data from models that project scenarios into the future. Example inputs: assumptions made about future developments of key parameters such as energy prices and GDP. Example outputs: projected electricity transmission, projected greenhouse gas emissions. Note that inputs to one model could be an output of another model and the other way around.",  # noqa
        "reference": "Contains sources, literature and auxiliary/helper tables that can help you with your work.",  # noqa
        "emission": "Data on emissions. Examples: total greenhouse gas emissions, CO2-emissions, energy-related CO2-emissions, methane emissions, air pollutants etc.",  # noqa
        "openstreetmap": "OpenStreetMap is a open project that collects and structures freely usable geodata and keeps them in a database for use by anyone. This data is available under a free license, the Open Database License.",  # noqa
        "policy": "Data on policies and measures. This could, for example, include a list of renewable energy policies per European Member State. It could also be a list of climate related policies and measures in a specific country.",  # noqa
    }

    # NOTE: tables maybe in mutliple topics, so
    # total_table_count <= sum(count per topic)
    total_table_count = tables.count()

    topics_descriptions_tablecounts = []
    # NOTE/TODO:WINGECHR: model_draft is not a proper topic
    # but currently, all unpublished datastes are displayed in frontend
    topics_descriptions_tablecounts.append(
        (
            TODO_PSEUDO_TOPIC_DRAFT,
            description[TODO_PSEUDO_TOPIC_DRAFT],
            tables.filter(is_publish=False).count(),
        )
    )

    # get a count of tables for each topics
    topics = Topic.objects.filter(tables__in=tables).annotate(
        table_count=Count("tables")
    )
    for topic in topics.order_by("name").all():
        count = topic.table_count  # type: ignore (see annotate above)
        total_table_count += count
        topics_descriptions_tablecounts.append(
            (topic.name, description[topic.name], count)
        )

    return render(
        request,
        "dataedit/dataedit_schemalist.html",
        {
            "total_table_count": total_table_count,
            "schemas": topics_descriptions_tablecounts,
            "query": searched_query_string,
            "tags": searched_tag_ids,
            "doc_oem_builder_link": EXTERNAL_URLS["tutorials_oemetabuilder"],
        },
    )


@login_required
def tag_overview_view(request: HttpRequest) -> HttpResponse:
    # if rename or adding of tag fails: display error message
    context = {
        "errorMsg": (
            "Tag name is not valid" if request.GET.get("status") == "invalid" else ""
        )
    }

    return render(
        request=request, template_name="dataedit/tag_overview.html", context=context
    )


@login_required
def tag_editor_view(request: HttpRequest, tag_pk: str | None = None) -> HttpResponse:
    tag = Tag.get_or_none(tag_pk or "")
    if tag:
        assigned = tag.tables.count() > 0
        return render(
            request=request,
            template_name="dataedit/tag_editor.html",
            context={
                "name": tag.name,
                "pk": tag.pk,
                "color_hex": tag.color_hex,
                "assigned": assigned,
            },
        )
    else:
        return render(
            request=request,
            template_name="dataedit/tag_editor.html",
            context={"name": "", "color_hex": "#000000", "assigned": False},
        )


@require_POST
@login_required
def tag_update_view(request: HttpRequest) -> HttpResponse:
    status = ""  # error status if operation fails

    if "submit_save" in request.POST:
        try:
            if "tag_id" in request.POST:
                id = request.POST["tag_id"]
                name = request.POST["tag_text"]
                color = request.POST["tag_color"]
                edit_tag(id, name, color)
            else:
                name = request.POST["tag_text"]
                color = request.POST["tag_color"]
                add_tag(name, color)
        except IntegrityError:
            # requested changes are not valid because of name conflicts
            status = "invalid"

    elif "submit_delete" in request.POST:
        id = request.POST["tag_id"]
        delete_tag(id)

    return redirect(reverse("dataedit:tags") + f"?status={status}")


@require_POST
@login_required
def tag_table_add_view(request: HttpRequest) -> HttpResponse:
    """
    Updates the tags on a table according to the tag values in request.
    The update will delete all tags that are not present
    in request and add all tags that are.

    :param request: A HTTP-request object sent by the Django framework.
        The *POST* field must contain the following values:
        * schema: The name of a schema
        * table: The name of a table
        * Any number of values that start with 'tag_' followed by the id of a tag.
    :return: Redirects to the previous page
    """
    table = get_or_403(request.POST, "table")
    table_obj = table_or_404(table=table)
    schema_name = table_obj.oedb_schema

    try:
        # check write permission
        assert_add_tag_permission(
            request.user, table, login.permissions.WRITE_PERM, schema=schema_name
        )
        tag_prefix = "tag_"
        tag_prefix_len = len(tag_prefix)
        tag_ids = {
            field[tag_prefix_len:]
            for field in request.POST
            if field.startswith(tag_prefix)
        }
        tags = Tag.objects.filter(pk__in=tag_ids)
        table_obj = Table.objects.get(name=table)
        table_obj.tags.clear()
        for tag in tags:
            table_obj.tags.add(tag)
        # TODO: we already do save in update_keywords_from_tags further down
        table_obj.save()

        update_keywords_from_tags(table_obj, schema=schema_name)

        messages.success(
            request,
            (
                "Successfully updated table tags! "
                "Please note that OEMetadata keywords and table tags are synchronized. "
                "When submitting new tags, you may notice automatic changes to the "
                'table tags on the OEP and/or the "Keywords" field in the metadata.'
            ),
        )
    except APIError as exp:
        messages.error(request, str(exp))
    except Exception:
        # generic error message
        messages.error(request, "Something went wrong")

    redirect_url = request.META.get("HTTP_REFERER") or reverse("dataedit:index")
    return redirect(redirect_url)


def metadata_widget_view(request: HttpRequest) -> HttpResponse:
    """
    A view to render the metadata widget for the dataedit app.
    The metadata widget is a small widget that can be embedded in other
    applications to display metadata information.

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        HttpResponse: Rendered HTML response for the metadata widget.
    """
    # TODO: schema and table should be in path?
    schema = request.GET.get("schema")
    table = request.GET.get("table")

    if schema is None or table is None:
        return JsonResponse(
            {"error": "Schema and table parameters are required."}, status=400
        )

    context = {
        "meta_api": reverse(
            "api:api_table_meta", kwargs={"schema": schema, "table": table}
        )
    }

    return render(request, "partials/metadata_viewer.html", context=context)


def tables_view(request: HttpRequest, topic: str) -> HttpResponse:
    """
    :param request: A HTTP-request object sent by the Django framework
    :param schema_name: Name of a schema
    :return: Renders the list of all tables in the specified schema
    """

    searched_query_string = request.GET.get("query")
    searched_tag_ids = request.GET.getlist("tags")

    Tag.increment_usage_count_many(searched_tag_ids)

    # find all tables (layzy query set) in this schema
    tables = find_tables(
        topic_name=topic,
        query_string=searched_query_string,
        tag_ids=searched_tag_ids,
    )

    tables = tables.order_by(
        F("date_updated").desc(nulls_last=True), "human_readable_name"
    )

    # paginate tables
    paginator = Paginator(tables, ITEMS_PER_PAGE)
    tables_paginated = paginator.get_page(get_page(request))

    return render(
        request,
        "dataedit/dataedit_tablelist.html",
        {
            "tables_paginated": tables_paginated,
            "query": searched_query_string,
            "tags": searched_tag_ids,
            "topic": topic,
            "doc_oem_builder_link": DOCUMENTATION_LINKS["oemetabuilder"],
        },
    )


def table_show_revision_view(
    request: HttpRequest, schema: str, table: str, date: str
) -> HttpResponse:
    table_obj = table_or_404(table=table)
    schema_name = table_obj.oedb_schema

    rev = TableRevision.objects.get(schema=schema_name, table=table, date=date)
    rev.last_accessed = timezone.now()
    rev.save()
    return send_dump(schema_name, table, date)


@require_POST
def table_view_save_view(request: HttpRequest, schema: str, table: str) -> HttpResponse:
    table_obj = table_or_404(table=table)
    schema_name = table_obj.oedb_schema

    post_name = request.POST.get("name")
    post_type = request.POST.get("type")
    post_id = request.POST.get("id")
    post_options = {}

    if post_type == "graph":
        # add x and y axis to post_options
        post_x_axis = request.POST.get("x-axis")
        y_axis_list = []
        for item in request.POST.items():
            item_name, item_value = item
            y_ax_prefix = "y-axis-"
            y_ax_prefix_len = len(y_ax_prefix)
            if item_name.startswith(y_ax_prefix) and item_value == "on":
                y_axis_list.append(item_name[y_ax_prefix_len:])
        post_options = {"x_axis": post_x_axis, "y_axis": y_axis_list}
    elif post_type == "map":
        # add location column info to options
        post_pos_type = request.POST.get("location_type")
        if post_pos_type == "single-column":
            post_geo_column = request.POST.get("geo_data")
            post_options = {"geo_type": "single-column", "geo_column": post_geo_column}
        elif post_pos_type == "lat_long":
            post_geo_lat = request.POST.get("geo_lat")
            post_geo_long = request.POST.get("geo_long")
            post_options = {
                "geo_type": "lat_long",
                "geo_lat": post_geo_lat,
                "geo_long": post_geo_long,
            }

    # update or create corresponding view
    if post_id:
        update_view = DBView.objects.filter(id=post_id).get()
        if post_name:
            update_view.name = post_name
        update_view.options = post_options
    else:
        update_view = DBView(
            name=post_name,
            type=post_type,
            options=post_options,
            table=table,
            schema=schema_name,
        )

    update_view.save()

    # create and update filters
    post_filter_json = request.POST.get("filter")
    if post_filter_json:
        post_filter = json.loads(post_filter_json)

        db_filter: DBFilter
        for db_filter in update_view.filter.all():
            # look for filters in the database, that aren't used anymore and delete them
            db_filter_is_used = False
            for defined_filter in post_filter:
                if "id" in defined_filter:
                    if db_filter.pk == defined_filter["id"]:
                        db_filter_is_used = True
                        break
            if not db_filter_is_used:
                db_filter.delete()

        for filter in post_filter:
            if post_id and "id" in filter:
                # filter is already defined and needs to be updated
                curr_filter = DBFilter.objects.filter(
                    id=filter["id"], view_id=post_id
                ).get()
                curr_filter.column = filter["column"]
                curr_filter.type = filter["type"]
                curr_filter.value = filter["value"]
                curr_filter.save()
            else:
                # create new filter
                curr_filter = DBFilter(
                    view=update_view,
                    column=filter["column"],
                    type=filter["type"],
                    value=filter["value"],
                )
                curr_filter.save()

    return redirect(
        reverse("dataedit:view", kwargs={"schema": schema_name, "table": table})
        + f"?view={update_view.pk}"
    )


def table_view_set_default_view(
    request: HttpRequest, schema: str, table: str
) -> HttpResponse:
    table_obj = table_or_404(table=table)
    schema_name = table_obj.oedb_schema

    # TODO: shouldnt this be POST only?
    post_id = request.GET.get("id")

    for view in DBView.objects.filter(schema=schema_name, table=table):
        if str(view.pk) == post_id:
            view.is_default = True
        else:
            view.is_default = False
        view.save()
    return redirect("dataedit:view", schema=schema_name, table=table)


def table_view_delete_view(
    request: HttpRequest, schema: str, table: str
) -> HttpResponse:
    table_obj = table_or_404(table=table)
    schema_name = table_obj.oedb_schema

    # TODO: shouldnt this be POST only?
    post_id = request.GET.get("id")

    view = DBView.objects.get(id=post_id, schema=schema_name, table=table)
    view.delete()

    return redirect("dataedit:view", schema=schema_name, table=table)


class TableGraphView(View):
    def get(self, request: HttpRequest, schema: str, table: str) -> HttpResponse:

        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        # get the columns id from the schema and the table
        columns = [(c, c) for c in describe_columns(schema_name, table).keys()]
        formset = GraphViewForm(columns=columns)

        return render(request, "dataedit/tablegraph_form.html", {"formset": formset})

    def post(self, request: HttpRequest, schema: str, table: str) -> HttpResponse:

        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        # save an instance of View, look at GraphViewForm fields in forms.py
        # for information to the options
        opt = dict(x=request.POST.get("column_x"), y=request.POST.get("column_y"))
        gview = DataViewModel.objects.create(
            name=request.POST.get("name"),
            table=table,
            type="graph",
            options=opt,
            is_default=request.POST.get("is_default", False),
        )
        gview.save()

        return redirect(
            reverse("dataedit:view", kwargs={"schema": schema_name, "table": table})
            + f"?view={gview.pk}"
        )


class TableMapView(View):
    def get(
        self, request: HttpRequest, schema: str, table: str, maptype: str
    ) -> HttpResponse:
        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        columns = [(c, c) for c in describe_columns(schema_name, table).keys()]
        if maptype == "latlon":
            form = LatLonViewForm(columns=columns)
        elif maptype == "geom":
            form = GeomViewForm(columns=columns)
        else:
            raise Http404

        return render(request, "dataedit/tablemap_form.html", {"form": form})

    def post(
        self, request: HttpRequest, schema: str, table: str, maptype: str
    ) -> HttpResponse:
        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        columns = [(c, c) for c in describe_columns(schema_name, table).keys()]
        if maptype == "latlon":
            form = LatLonViewForm(request.POST, columns=columns)
            options = dict(lat=request.POST.get("lat"), lon=request.POST.get("lon"))
        elif maptype == "geom":
            form = GeomViewForm(request.POST, columns=columns)
            options = dict(geom=request.POST.get("geom"))
        else:
            raise Http404

        form.table = table
        form.options = options
        if form.is_valid():
            view_id = form.save(commit=True)
            return redirect(
                reverse("dataedit:view", kwargs={"schema": schema_name, "table": table})
                + f"?view={view_id}"
            )
        else:
            return self.get(
                request=request, schema=schema_name, table=table, maptype=maptype
            )


class TableDataView(View):
    """This class handles the GET and POST requests for the main page of data edit.

    This view is displayed when a table is clicked on after choosing a schema
    on the website

    Initializes the session data (if necessary)
    """

    # TODO Check if this hits bad in performance
    @method_decorator(never_cache)
    def get(self, request: HttpRequest, schema: str, table: str) -> HttpResponse:
        """
        Collects the following information on the specified table:
            * Postgresql comment on this table
            * A list of all columns
            * A list of all revisions of this table

        :param request: An HTTP-request object sent by the Django framework
        :param schema: Name of a schema
        :param table: Name of a table stored in this schema
        :return:
        """

        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        metadata = load_metadata_from_db(table=table)
        table_obj = Table.load(name=table)
        if table_obj is None:
            raise Http404("Table object could not be loaded")

        # TODO: Adapt this stuff to v2
        from dataedit.metadata import TEMPLATE_V1_5

        def iter_oem_key_order(metadata: dict):
            oem_151_key_order = [key for key in TEMPLATE_V1_5.keys()]
            for key in oem_151_key_order:
                yield key, metadata.get(key)

        ordered_oem_151 = {key: value for key, value in iter_oem_key_order(metadata)}
        # TODO: refactor the widget
        meta_widget = MetaDataWidget(ordered_oem_151)
        revisions = []

        api_changes = change_requests(schema_name, table)
        data = api_changes.get("data")
        display_message = api_changes.get("display_message")
        display_items = api_changes.get("display_items")

        is_admin = False
        can_add = False
        user: login_models.myuser = request.user  # type: ignore
        if request.user and not request.user.is_anonymous:
            is_admin = user.has_admin_permissions(table=table)
            level = user.get_table_permission_level(table_obj)
            can_add = level >= login.permissions.WRITE_PERM

        table_label = table_obj.human_readable_name

        table_views = DBView.objects.filter(table=table)
        default = DBView(name="default", type="table", table=table)
        view_id = request.GET.get("view")

        embargo = Embargo.objects.filter(table=table_obj).first()
        if embargo and embargo.date_ended:
            now = timezone.now()
            if embargo.date_ended > now:
                embargo_time_left = embargo.date_ended - now
            else:
                embargo_time_left = "The embargo is over"
        else:
            embargo_time_left = "No embargo data available"

        if view_id == "default":
            current_view = default
            current_view.save()
        else:
            try:
                # at first, try to use the view, that is passed as get argument
                current_view = table_views.get(id=view_id)
            except ObjectDoesNotExist:
                current_view = default
                current_view.save()

        table_views = list(chain((default,), table_views))

        #########################################################
        #   Get open peer review process related metadata       #
        #########################################################

        # Context data for the open peer review (data view side panel)
        opr_context = {}
        # Context data for review result tab
        opr_result_context = {}
        # maybe call the update also on this view to show the days open on page
        opr_manager = PeerReviewManager()
        reviews = opr_manager.filter_opr_by_table(table=table)

        opr_context = {
            "contributor": PeerReviewManager.load_contributor(table=table),
            "reviewer": PeerReviewManager.load_reviewer(table=table),
            "opr_enabled": False,
            # oemetadata
            # is not None,  # check if the table has the metadata
        }

        opr_result_context = {}
        if reviews.exists():
            latest_review: PeerReview = reviews.last()  # type:ignore (reviews.exists())
            opr_manager.update_open_since(opr=latest_review)
            current_reviewer = opr_manager.load(latest_review).current_reviewer
            opr_context.update(
                {
                    "opr_id": latest_review.pk,
                    "opr_current_reviewer": current_reviewer,
                    "is_finished": latest_review.is_finished,
                }
            )

            if latest_review.is_finished:
                badge = (latest_review.review or {}).get("badge")
                date_finished = latest_review.date_finished
                opr_result_context.update(
                    {
                        "badge": badge,
                        "review_url": None,
                        "date_finished": date_finished,
                        "review_id": latest_review.pk,
                        "finished": latest_review.is_finished,
                        "review_exists": True,
                    }
                )
        else:
            opr_context.update({"opr_id": None, "opr_current_reviewer": None})
            opr_result_context.update({"review_exists": False, "finished": False})

        #########################################################
        #   Construct the context object for the template       #
        #########################################################

        context_dict = {
            "meta_widget": meta_widget.render(),
            "revisions": revisions,
            "kinds": ["table", "map", "graph"],
            "table": table,
            "table_obj": table_obj,
            "schema": schema_name,  # TODO:remove
            "table_label": table_label,
            # "tags": tags,
            "data": data,
            "display_message": display_message,
            "display_items": display_items,
            "views": table_views,
            "filter": current_view.filter.all(),
            "current_view": current_view,
            "is_admin": is_admin,
            "can_add": can_add,
            "host": request.get_host(),
            "opr": opr_context,
            "opr_result": opr_result_context,
            "embargo_time_left": embargo_time_left,
        }

        return render(request, "dataedit/dataview.html", context=context_dict)

    def post(self, request: HttpRequest, schema: str, table: str) -> HttpResponse:
        """
        Handles the behaviour if a .csv-file is sent to the view of a table.
        The contained datasets are inserted into the corresponding table via
        the API.
        :param request: A HTTP-request object sent by the Django framework
        :param schema: Name of a schema
        :param table: Name of a table
        :return: Redirects to the view of the table the data was sent to.
        """
        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        if request.POST and request.FILES:
            csvfile = TextIOWrapper(
                request.FILES["csv_file"].file, encoding=request.encoding
            )

            reader = csv.DictReader(csvfile, delimiter=",")

            data_insert(
                {
                    "schema": schema_name,
                    "table": table,
                    "method": "values",
                    "values": reader,
                },
                {"user": request.user},
            )
        return redirect("dataedit:view", schema=schema_name, table=table)


class TablePermissionView(View):
    """This method handles the GET requests for the main page of data edit.
    Initialises the session data (if necessary)
    """

    def get(self, request: HttpRequest, schema: str, table: str) -> HttpResponse:

        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        user_perms = login_models.UserPermission.objects.filter(table=table_obj)
        group_perms = login_models.GroupPermission.objects.filter(table=table_obj)
        is_admin = False
        can_add = False
        can_remove = False
        level = login.permissions.NO_PERM
        user: login_models.myuser = request.user  # type: ignore
        if not user.is_anonymous:
            level = user.get_table_permission_level(table_obj)
            is_admin = level >= login.permissions.ADMIN_PERM
            can_add = level >= login.permissions.WRITE_PERM
            can_remove = level >= login.permissions.DELETE_PERM
        return render(
            request,
            "dataedit/table_permissions.html",
            {
                "table": table,
                "schema": schema_name,
                "user_perms": user_perms,
                "group_perms": group_perms,
                "choices": login_models.TablePermission.choices,
                "can_add": can_add,
                "can_remove": can_remove,
                "is_admin": is_admin,
                "own_level": level,
            },
        )

    def post(self, request: HttpRequest, schema: str, table: str) -> HttpResponse:
        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        user: login_models.myuser = request.user  # type: ignore
        if (
            user.is_anonymous
            or user.get_table_permission_level(table_obj) < login.permissions.ADMIN_PERM
        ):
            raise PermissionDenied
        if request.POST["mode"] == "add_user":
            return self.__add_user(request, schema_name, table)
        if request.POST["mode"] == "alter_user":
            return self.__change_user(request, schema_name, table)
        if request.POST["mode"] == "remove_user":
            return self.__remove_user(request, schema_name, table)
        if request.POST["mode"] == "add_group":
            return self.__add_group(request, schema_name, table)
        if request.POST["mode"] == "alter_group":
            return self.__change_group(request, schema_name, table)
        if request.POST["mode"] == "remove_group":
            return self.__remove_group(request, schema_name, table)
        else:
            raise NotImplementedError()

    def __add_user(self, request: HttpRequest, schema: str, table: str):

        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        user_name = request.POST.get("name")
        # Check if the user name is empty
        if not user_name:
            # Return an HTTP 400 Bad Request response
            return HttpResponseBadRequest("User name is required.")

        user = login_models.myuser.objects.filter(name=user_name).first()

        p, _ = login_models.UserPermission.objects.get_or_create(
            holder=user, table=table_obj
        )
        p.save()
        return self.get(request, schema_name, table)

    def __change_user(self, request: HttpRequest, schema: str, table: str):

        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        user_id = request.POST.get("user_id")
        # Check if the user id is empty
        if not user_id:
            # Return an HTTP 400 Bad Request response
            return HttpResponseBadRequest("User id is required.")

        user = login_models.myuser.objects.filter(id=user_id).first()

        p = get_object_or_404(login_models.UserPermission, holder=user, table=table_obj)
        p.level = int(request.POST["level"])
        p.save()
        return self.get(request, schema_name, table)

    def __remove_user(self, request: HttpRequest, schema: str, table: str):

        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        user_id = request.POST.get("user_id")
        # Check if the user id is empty
        if not user_id:
            # Return an HTTP 400 Bad Request response
            return HttpResponseBadRequest("User id is required.")

        user = get_object_or_404(login_models.myuser, id=user_id)

        p = get_object_or_404(login_models.UserPermission, holder=user, table=table_obj)
        p.delete()
        return self.get(request, schema_name, table)

    def __add_group(self, request: HttpRequest, schema: str, table: str):

        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        group_name = request.POST.get("name")
        # Check if the group name is empty
        if not group_name:
            # Return an HTTP 400 Bad Request response
            return HttpResponseBadRequest("Group name is required.")

        group = get_object_or_404(login_models.UserGroup, name=group_name)

        p, _ = login_models.GroupPermission.objects.get_or_create(
            holder=group, table=table_obj
        )
        p.save()
        return self.get(request, schema_name, table)

    def __change_group(self, request: HttpRequest, schema: str, table: str):

        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        group_id = request.POST.get("group_id")
        if not group_id:
            # Return an HTTP 400 Bad Request response
            return HttpResponseBadRequest("Group id is required.")

        group = get_object_or_404(login_models.UserGroup, id=group_id)

        p = get_object_or_404(
            login_models.GroupPermission, holder=group, table=table_obj
        )
        p.level = int(request.POST["level"])
        p.save()
        return self.get(request, schema_name, table)

    def __remove_group(self, request: HttpRequest, schema: str, table: str):

        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        group_id = request.POST.get("group_id")
        if not group_id:
            # Return an HTTP 400 Bad Request response
            return HttpResponseBadRequest("Group id is required.")

        group = get_object_or_404(login_models.UserGroup, id=group_id)

        p = get_object_or_404(
            login_models.GroupPermission, holder=group, table=table_obj
        )
        p.delete()
        return self.get(request, schema_name, table)


class TableWizardView(LoginRequiredMixin, View):
    """View for the upload wizard (create tables, upload csv)."""

    def get(
        self, request: HttpRequest, schema: str | None = None, table: str | None = None
    ) -> HttpResponse:
        """Handle GET request (render the page)."""

        can_add = False
        columns = None
        # pk_fields = None
        n_rows = None
        if table:

            table_obj = table_or_404(table=table)
            schema_name = table_obj.oedb_schema

            user: login_models.myuser = request.user  # type: ignore
            level = user.get_table_permission_level(table_obj)
            can_add = level >= login.permissions.WRITE_PERM
            columns = get_column_description(schema_name, table)
            # get number of rows
            sql = 'SELECT COUNT(*) FROM "{schema}"."{table}"'.format(
                schema=schema_name, table=table
            )
            res = perform_sql(sql)
            n_rows = res["result"].fetchone()[0]
        else:
            schema_name = SCHEMA_DATA

        context = {
            "config": json.dumps(
                {  # pass as json string
                    "canAdd": can_add,
                    "columns": columns,
                    "schema": schema_name,
                    "table": table,
                    "nRows": n_rows,
                }
            ),
            "schema": schema_name,
            "table": table,
            "can_add": can_add,
            "wizard_academy_link": EXTERNAL_URLS["tutorials_wizard"],
            "create_database_conform_data": EXTERNAL_URLS[
                "tutorials_create_database_conform_data"
            ],
        }

        return render(request, "dataedit/wizard.html", context=context)


class TableMetaEditView(LoginRequiredMixin, View):
    """Metadata editor (cliet side json forms)."""

    def get(self, request: HttpRequest, schema: str, table: str) -> HttpResponse:
        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        columns = get_column_description(schema_name, table)

        can_add = False

        user: login_models.myuser = request.user  # type: ignore
        if not user.is_anonymous:
            level = user.get_table_permission_level(table_obj)
            can_add = level >= login.permissions.WRITE_PERM

        url_table_id = request.build_absolute_uri(
            reverse("dataedit:view", kwargs={"schema": schema_name, "table": table})
        )

        context_dict = {
            "schema": schema_name,
            "table": table,
            "config": json.dumps(
                {
                    "schema": schema_name,
                    "table": table,
                    "columns": columns,
                    "url_table_id": url_table_id,
                    "url_api_meta": reverse(
                        "api:api_table_meta",
                        kwargs={"schema": schema_name, "table": table},
                    ),
                    "url_view_table": reverse(
                        "dataedit:view", kwargs={"schema": schema_name, "table": table}
                    ),
                    "cancle_url": get_cancle_state(self.request),
                    "standalone": False,
                }
            ),
            "can_add": can_add,
            "doc_links": DOCUMENTATION_LINKS,
            "oem_key_desc": EXTERNAL_URLS["oemetadata_key_description"],
            "oemetadata_tutorial": EXTERNAL_URLS["tutorials_oemetadata"],
            "oemetabuilder_tutorial": EXTERNAL_URLS["tutorials_oemetabuilder"],
        }

        return render(
            request,
            "dataedit/meta_edit.html",
            context=context_dict,
        )


class TablePeerReviewView(LoginRequiredMixin, View):
    """
    A view handling the peer review of metadata. This view supports loading,
    parsing, sorting metadata, and handling GET and POST requests for peer review.
    """

    def load_json(self, schema: str, table: str, review_id=None):
        """
        Load JSON metadata from the database. If the review_id is available
        then load the metadata form the peer review instance and not from the
        table. This avoids changes to the metadata that is or was reviewed.

        Args:
            schema (str): The schema of the table.
            table (str): The name of the table.
            review_id (int): Id of a peer review in the django database

        Returns:
            dict: Loaded oemetadata.
        """
        metadata = {}
        if review_id is None:
            metadata = load_metadata_from_db(table=table)
        elif review_id:
            opr = PeerReviewManager.get_opr_by_id(opr_id=review_id)
            metadata = opr.oemetadata

        return metadata

    def load_json_schema(self):
        """
        Load the JSON schema used for validating metadata.

        Note:
            Update this method if a new oemetadata version is released.

        Returns:
            dict: JSON schema.
        """
        json_schema = OEMETADATA_V20_SCHEMA
        return json_schema

    def parse_keys(self, val, old=""):
        """
        Recursively parse keys from a nested dictionary or list and return them
        as a list of dictionaries.

        Args:
            val (dict or list): The input dictionary or list to parse.
            old (str, optional): The prefix for nested keys. Defaults to an
                empty string.

        Returns:
            list: A list of dictionaries, each containing 'field' and 'value'
                keys.
        """
        lines = []
        if isinstance(val, dict):
            for k in val.keys():
                lines += self.parse_keys(val[k], old + "." + str(k))
        elif isinstance(val, list):
            if not val:
                # handles empty list
                lines += [{"field": old[1:], "value": str(val)}]
            else:
                for i, k in enumerate(val):
                    lines += self.parse_keys(
                        k, old + "." + str(i)
                    )  # handles user value
        else:
            lines += [{"field": old[1:], "value": str(val)}]
        return lines

    def sort_in_category(self, schema: str, table: str, oemetadata):
        """
        Group flattened OEMetadata v2 fields into thematic buckets and attach
        placeholders required by the review UI.

        Each entry has six keys:
        {
          "field": "<dot-path>",
          "label": "<display label without 'resources.<idx>.'>",
          "value": "<current value>",
          "newValue": "",
          "reviewer_suggestion": "",
          "suggestion_comment": ""
        }
        """

        flattened = self.parse_keys(oemetadata)
        flattened = [
            item for item in flattened if item["field"].startswith("resources.")
        ]

        bucket_map = {
            "spatial": "spatial",
            "temporal": "temporal",
            "sources": "source",
            "licenses": "license",
        }

        def make_label(dot_path: str) -> str:
            # remove leading resources.<idx>.
            trimmed = re.sub(r"^resources\.[0-9]+\.", "", dot_path)
            parts = trimmed.split(".")
            out = []
            for p in parts:
                if p in {"@id", "@type"}:
                    out.append(p)
                else:
                    out.append(p.replace("_", " "))
            if out:
                out[0] = out[0][:1].upper() + out[0][1:]
            return " ".join(out)

        tmp = defaultdict(list)

        for item in flattened:
            raw_key = item["field"]
            parts = raw_key.split(".")

            if parts[0] == "resources" and len(parts) >= 3:
                root = parts[2]
            else:
                root = parts[0]

            bucket = bucket_map.get(root, "general")

            tmp[bucket].append(
                {
                    "field": raw_key,
                    "label": make_label(raw_key),
                    "value": item["value"],
                    "newValue": "",
                    "reviewer_suggestion": "",
                    "suggestion_comment": "",
                }
            )

        return {
            "general": tmp["general"],
            "spatial": tmp["spatial"],
            "temporal": tmp["temporal"],
            "source": tmp["source"],
            "license": tmp["license"],
        }

    def get_all_field_descriptions(self, json_schema, prefix=""):
        """
        Collects the field title, descriptions, examples, and badge information
        for each field of the oemetadata from the JSON schema and prepares them
        for further processing.

        Args:
            json_schema (dict): The JSON schema to extract field descriptions
                from.
            prefix (str, optional): The prefix for nested keys. Defaults to an
                empty string.

        Returns:
            dict: A dictionary containing field descriptions, examples, and
                other information.
        """

        field_descriptions = {}

        def extract_descriptions(properties, prefix=""):
            for field, value in properties.items():
                key = f"{prefix}.{field}" if prefix else field

                if any(
                    attr in value
                    for attr in ["description", "examples", "example", "badge", "title"]
                ):
                    field_descriptions[key] = {}
                    if "description" in value:
                        field_descriptions[key]["description"] = value["description"]
                    # Prefer v2 "examples" (array) over v1 "example" (single value)
                    if "examples" in value and value["examples"]:
                        # v2: first item of the examples array
                        field_descriptions[key]["example"] = value["examples"][0]
                    elif "example" in value:
                        # v1 fallback
                        field_descriptions[key]["example"] = value["example"]
                    if "badge" in value:
                        field_descriptions[key]["badge"] = value["badge"]
                    if "title" in value:
                        field_descriptions[key]["title"] = value["title"]
                if "properties" in value:
                    new_prefix = f"{prefix}.{field}" if prefix else field
                    extract_descriptions(value["properties"], new_prefix)
                if "items" in value:
                    new_prefix = f"{prefix}.{field}" if prefix else field
                    if "properties" in value["items"]:
                        extract_descriptions(value["items"]["properties"], new_prefix)

        extract_descriptions(json_schema["properties"], prefix)
        return field_descriptions

    def get(
        self,
        request: HttpRequest,
        schema: str,
        table: str,
        review_id: int | None = None,
    ) -> HttpResponse:
        """
        Handle GET requests for peer review.
        Loads necessary data and renders the review template.

        Args:
            request (HttpRequest): The incoming HTTP GET request.
            schema (str): The schema of the table.
            table (str): The name of the table.
            review_id (int, optional): The ID of the review. Defaults to None.

        Returns:
            HttpResponse: Rendered HTML response.
        """

        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        # review_state = PeerReview.is_finished  # TODO: Use later
        json_schema = self.load_json_schema()
        can_add = False
        table_obj = Table.load(name=table)
        field_descriptions = self.get_all_field_descriptions(json_schema)

        # Check user permissions
        user: login_models.myuser = request.user  # type: ignore
        if not user.is_anonymous:
            level = user.get_table_permission_level(table_obj)
            can_add = level >= login.permissions.WRITE_PERM

        oemetadata = self.load_json(schema_name, table, review_id)
        metadata = self.sort_in_category(
            schema_name, table, oemetadata=oemetadata
        )  # Generate URL for peer_review_reviewer
        if review_id is not None:
            url_peer_review = reverse(
                "dataedit:peer_review_reviewer",
                kwargs={"schema": schema_name, "table": table, "review_id": review_id},
            )
            opr_review = PeerReviewManager.get_opr_by_id(opr_id=review_id)

            existing_review = (opr_review.review or {}).get("reviews", [])
            review_finished = opr_review.is_finished
            categories = [
                "general",
                "spatial",
                "temporal",
                "source",
                "license",
            ]
            state_dict = process_review_data(
                review_data=existing_review, metadata=metadata, categories=categories
            )
        else:
            url_peer_review = reverse(
                "dataedit:peer_review_create",
                kwargs={"schema": schema_name, "table": table},
            )
            # existing_review={}
            state_dict = None
            review_finished = None

        config_data = {
            "can_add": can_add,
            "url_peer_review": url_peer_review,
            "url_table": reverse(
                "dataedit:view", kwargs={"schema": schema_name, "table": table}
            ),
            "topic": schema_name,
            "table": table,
            "review_finished": review_finished,
            "review_id": review_id,
        }
        context_meta = {
            # need this here as json.dumps breaks the template syntax access
            # like {{ config.table }} now you can use {{ table }}
            "table": table,
            "topic": table_obj.topics,
            "config": json.dumps(config_data),
            "meta": metadata,
            "json_schema": json_schema,
            "field_descriptions_json": json.dumps(field_descriptions),
            "state_dict": json.dumps(state_dict),
            "review_finished": review_finished,
            "review_id": review_id,
        }
        return render(request, "dataedit/opr_review.html", context=context_meta)

    def post(
        self, request: HttpRequest, schema: str, table: str, review_id=None
    ) -> HttpResponse:
        """
        Handle POST requests for submitting reviews by the reviewer.

        This method:
        - Creates (or saves) reviews in the PeerReview table.
        - Updates the review finished attribute in the dataedit.Tables table,
            indicating that the table can be moved from the model draft topic.

        Missing parts:
        - once the opr is finished (all field reviews agreed on)
        - merge field review results to metadata on table
        - awarde a badge
            - is field filled in?
            - calculate the badge by comparing filled fields
              and the badges form metadata schema

        Args:
            request (HttpRequest): The incoming HTTP POST request.
            schema (str): The schema of the table.
            table (str): The name of the table.
            review_id (int, optional): The ID of the review. Defaults to None.

        Returns:
            HttpResponse: Rendered HTML response for the review.

        Raises:
            JsonResponse: If any error occurs, a JsonResponse containing the
            error message is raised.

        Note:
            - There are some missing parts in this method. Once the review process
                is finished (all field reviews agreed on), it should merge field
                review results to metadata on the table and award a badge based
                on certain criteria.
            - A notification should be sent to the user if he/she can't review tables
            for which he/she is the table holder (TODO).
            - After a review is finished, the table's metadata is updated, and the table
            can be moved to a different schema or topic (TODO).
        """
        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        context = {}
        user: login_models.myuser = request.user  # type: ignore

        # get the review data and additional application metadata
        # from user peer review submit/save
        review_data = json.loads(request.body)
        if review_id:
            contributor_review = PeerReview.objects.filter(id=review_id).first()
            if contributor_review:
                contributor_review_data = (contributor_review.review or {}).get(
                    "reviews", []
                )
                review_data["reviewData"]["reviews"].extend(contributor_review_data)

        # The type can be "save" or "submit" as this triggers different behavior
        review_post_type = review_data.get("reviewType")
        # The opr datamodel that includes the field review data and metadata
        review_datamodel = review_data.get("reviewData")
        review_finished = review_datamodel.get("reviewFinished")
        # TODO: Send a notification to the user that he can't review tables
        # he is the table holder.
        if review_post_type == "delete":
            return delete_peer_review(review_id)

        contributor = PeerReviewManager.load_contributor(table=table)

        if contributor is not None:
            # Überprüfen, ob ein aktiver PeerReview existiert
            active_peer_review = PeerReview.load(table=table)
            if active_peer_review is None or active_peer_review.is_finished:
                # Kein aktiver PeerReview vorhanden
                # oder der aktive PeerReview ist abgeschlossen
                table_review = PeerReview(
                    table=table,
                    is_finished=review_finished,
                    review=review_datamodel,
                    reviewer=user,
                    contributor=contributor,
                    oemetadata=load_metadata_from_db(table=table),
                )
                table_review.save(review_type=review_post_type)
            else:
                # Aktiver PeerReview ist vorhanden ... aktualisieren
                current_review_data = active_peer_review.review
                merged_review_data = merge_field_reviews(
                    current_json=current_review_data, new_json=review_datamodel
                )

                # Set new review values and update existing review
                active_peer_review.review = merged_review_data
                active_peer_review.reviewer = user  # type:ignore TODO why type warning?
                active_peer_review.contributor = contributor  # type:ignore TODO
                active_peer_review.update(review_type=review_post_type)
        else:
            error_msg = (
                "Failed to retrieve any user that identifies "
                f"as table holder for the current table: {table}!"
            )
            return JsonResponse({"error": error_msg}, status=400)

        # TODO: Check for schema/topic as reviewed finished also indicates the table
        # needs to be or has to be moved.
        if review_finished is True:
            review_table = Table.load(name=table)
            review_table.set_is_reviewed()
            metadata = self.load_json(schema_name, table, review_id=review_id)
            updated_metadata = recursive_update(metadata, review_data)
            save_metadata_to_db(schema_name, table, updated_metadata)
            active_peer_review = PeerReview.load(table=table)

            if active_peer_review:
                updated_oemetadata = recursive_update(
                    active_peer_review.oemetadata, review_data
                )
                active_peer_review.oemetadata = updated_oemetadata
                active_peer_review.save()

            # TODO: also update reviewFinished in review datamodel json

        return render(request, "dataedit/opr_review.html", context=context)


class TablePeerRreviewContributorView(TablePeerReviewView):
    """
    A view handling the contributor's side of the peer review process.
    This view supports rendering the review template and handling GET and
    POST requests for contributor's review.
    """

    def get(
        self, request: HttpRequest, schema: str, table: str, review_id: int
    ) -> HttpResponse:
        """
        Handle GET requests for contributor's review. Loads necessary data and
        renders the contributor review template.

        Args:
            request (HttpRequest): The incoming HTTP GET request.
            schema (str): The schema of the table.
            table (str): The name of the table.
            review_id (int): The ID of the review.

        Returns:
            HttpResponse: Rendered HTML response for contributor review.
        """
        table_obj = table_or_404(table=table)
        schema_name = table_obj.oedb_schema

        can_add = False
        peer_review = PeerReview.objects.get(id=review_id)
        table_obj = Table.load(peer_review.table)
        user: login_models.myuser = request.user  # type: ignore
        if not user.is_anonymous:
            level = user.get_table_permission_level(table_obj)
            can_add = level >= login.permissions.WRITE_PERM
        oemetadata = self.load_json(schema_name, table, review_id)
        metadata = self.sort_in_category(schema_name, table, oemetadata=oemetadata)
        json_schema = self.load_json_schema()
        field_descriptions = self.get_all_field_descriptions(json_schema)
        review_data = (peer_review.review or {}).get("reviews", [])

        categories = [
            "general",
            "spatial",
            "temporal",
            "source",
            "license",
        ]
        state_dict = process_review_data(
            review_data=review_data, metadata=metadata, categories=categories
        )
        context_meta = {
            "config": json.dumps(
                {
                    "can_add": can_add,
                    "url_peer_review": reverse(
                        "dataedit:peer_review_contributor",
                        kwargs={
                            "schema": schema_name,
                            "table": table,
                            "review_id": review_id,
                        },
                    ),
                    "url_table": reverse(
                        "dataedit:view", kwargs={"schema": schema_name, "table": table}
                    ),
                    "topic": schema_name,
                    "table": table,
                }
            ),
            "table": table,
            "topic": schema_name,
            "meta": metadata,
            "json_schema": json_schema,
            "field_descriptions_json": json.dumps(field_descriptions),
            "state_dict": json.dumps(state_dict),
        }
        return render(request, "dataedit/opr_contributor.html", context=context_meta)

    def post(
        self, request: HttpRequest, schema: str, table: str, review_id: int
    ) -> HttpResponse:
        """
        Handle POST requests for contributor's review. Merges and updates
        the review data in the PeerReview table.

        Args:
            request (HttpRequest): The incoming HTTP POST request.
            schema (str): The schema of the table.
            table (str): The name of the table.
            review_id (int): The ID of the review.

        Returns:
            HttpResponse: Rendered HTML response for contributor review.

        """
        # table_obj = table_or_404(table=table)
        # TODO: why unused argument "table"?

        context = {}
        if request.method == "POST":
            review_data = json.loads(request.body)
            review_post_type = review_data.get("reviewType")
            review_datamodel = review_data.get("reviewData")
            current_opr = PeerReviewManager.get_opr_by_id(opr_id=review_id)
            existing_reviews = current_opr.review
            merged_review = merge_field_reviews(
                current_json=existing_reviews, new_json=review_datamodel
            )

            current_opr.review = merged_review
            current_opr.update(review_type=review_post_type)

        return render(request, "dataedit/opr_contributor.html", context=context)
