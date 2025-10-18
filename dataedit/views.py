"""
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
import os
import re
from functools import reduce
from io import TextIOWrapper
from itertools import chain
from operator import add
from subprocess import call
from typing import Iterable
from wsgiref.util import FileWrapper

import sqlalchemy as sqla
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.search import SearchQuery
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Count, Q, QuerySet
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_str
from django.views.decorators.cache import never_cache
from django.views.generic import View
from oemetadata.v2.v20.schema import OEMETADATA_V20_SCHEMA
from sqlalchemy.orm import sessionmaker

import api.parser
import oeplatform.securitysettings as sec
from api import actions, utils
from dataedit.forms import GeomViewForm, GraphViewForm, LatLonViewForm
from dataedit.helper import (
    delete_peer_review,
    merge_field_reviews,
    process_review_data,
    recursive_update,
)
from dataedit.metadata import load_metadata_from_db, save_metadata_to_db
from dataedit.metadata.widget import MetaDataWidget
from dataedit.models import Embargo
from dataedit.models import Filter as DBFilter
from dataedit.models import PeerReview, PeerReviewManager, Table, Tag, Topic
from dataedit.models import View as DBView
from login import models as login_models
from oeplatform.securitysettings import SCHEMA_DATA, SCHEMA_DEFAULT_TEST_SANDBOX
from oeplatform.settings import DOCUMENTATION_LINKS, EXTERNAL_URLS

from .models import TableRevision
from .models import View as DataViewModel

# TODO: WINGECHR: model_draft is not a topic, but currently,
# frontend still usses it to filter / search for unpublished data
TODO_PSEUDO_TOPIC_DRAFT = "model_draft"

session = None

""" This is the initial view that initialises the database connection """
schema_whitelist = [
    "boundaries",
    "climate",
    "demand",
    "economy",
    "emission",
    "environment",
    "grid",
    "model_draft",
    "openstreetmap",
    "policy",
    "reference",
    "scenario",
    "society",
    "supply",
    SCHEMA_DATA,
]


def admin_constraints(request):
    """
    Way to apply changes
    :param request:
    :return:
    """
    post_dict = dict(request.POST)
    action = post_dict.get("action")[0]
    id = post_dict.get("id")[0]
    schema = post_dict.get("schema")[0]
    table = post_dict.get("table")[0]

    print("action: " + action)
    print("id: " + id)

    if "deny" in action:
        actions.remove_queued_constraint(id)
    elif "apply" in action:
        actions.apply_queued_constraint(id)

    return redirect(
        "/dataedit/view/{schema}/{table}".format(schema=schema, table=table)
    )


def admin_columns(request):
    """
    Way to apply changes
    :param request:
    :return:
    """

    post_dict = dict(request.POST)
    action = post_dict.get("action")[0]
    id = post_dict.get("id")[0]
    schema = post_dict.get("schema")[0]
    table = post_dict.get("table")[0]

    print("action: " + action)
    print("id: " + id)

    if "deny" in action:
        actions.remove_queued_column(id)
    elif "apply" in action:
        actions.apply_queued_column(id)

    return redirect(
        "/dataedit/view/{schema}/{table}".format(schema=schema, table=table)
    )


def change_requests(schema, table):
    """
    Loads the dataedit admin interface
    :param request:
    :return:
    """
    # I want to display old and new data, if different.

    display_message = None
    api_columns = actions.get_column_changes(reviewed=False, schema=schema, table=table)
    api_constraints = actions.get_constraints_changes(
        reviewed=False, schema=schema, table=table
    )

    # print(api_columns)
    # print(api_constraints)

    # cache = dict()
    data = dict()

    data["api_columns"] = {}
    data["api_constraints"] = {}

    keyword_whitelist = [
        "column_name",
        "c_table",
        "c_schema",
        "reviewed",
        "changed",
        "id",
    ]

    old_description = actions.describe_columns(schema, table)

    for change in api_columns:
        name = change["column_name"]
        id = change["id"]

        # Identifing over 'new'.
        if change.get("new_name") is not None:
            change["column_name"] = change["new_name"]

        old_cd = old_description.get(name)

        data["api_columns"][id] = {}
        data["api_columns"][id]["old"] = {}

        if old_cd is not None:
            old = api.parser.parse_scolumnd_from_columnd(
                schema, table, name, old_description.get(name)
            )

            for key in list(change):
                value = change[key]
                if key not in keyword_whitelist and (
                    value is None or value == old[key]
                ):
                    old.pop(key)
                    change.pop(key)
            data["api_columns"][id]["old"] = old
        else:
            data["api_columns"][id]["old"]["c_schema"] = schema
            data["api_columns"][id]["old"]["c_table"] = table
            data["api_columns"][id]["old"]["column_name"] = name

        data["api_columns"][id]["new"] = change

    for i in range(len(api_constraints)):
        value = api_constraints[i]
        id = value.get("id")
        if (
            value.get("reference_table") is None
            or value.get("reference_column") is None
        ):
            value.pop("reference_table")
            value.pop("reference_column")

        data["api_constraints"][id] = value

    display_style = [
        "c_schema",
        "c_table",
        "column_name",
        "not_null",
        "data_type",
        "reference_table",
        "constraint_parameter",
        "reference_column",
        "action",
        "constraint_type",
        "constraint_name",
    ]

    return {
        "data": data,
        "display_items": display_style,
        "display_message": display_message,
    }


def listschemas(request):
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
        count = topic.table_count
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


def get_session_query():
    engine = actions._get_engine()
    conn = engine.connect()
    Session = sessionmaker()
    session = Session(bind=conn)
    return session.query


def find_tables(
    topic_name: str | None = None,
    query_string: str | None = None,
    tag_ids: list[str] | None = None,
) -> QuerySet[Table]:
    """find tables given search criteria

    Args:
        topic_name (str, optional): only tables in this topic
        query_string (str, optional): user search term
        tag_ids (list, optional): list of tag ids

    Returns:
        QuerySet of Table objetcs
    """

    # define search filter (will be combined with AND):
    # only show tables NOT in sandbox
    filters = [Q(is_sandbox=False)]

    if topic_name:
        # TODO: WINGECHR: model_draft is not a topic, but currently,
        # frontend still usses it to filter / search for unpublished data
        if topic_name == TODO_PSEUDO_TOPIC_DRAFT:
            filters.append(Q(is_publish=False))
        else:
            filters.append(Q(topics=topic_name))

    if query_string:  # filter by search terms
        filters.append(
            Q(
                search=SearchQuery(
                    " & ".join(p + ":*" for p in re.findall(r"[\w]+", query_string)),
                    search_type="raw",
                )
            )
        )

    if tag_ids:  # filter by tags:
        # unfortunately, tags are no longer in django tables,
        # so we cannot filter directly
        # instead, we load all table names that match the given tags

        # find tables (in schema), that use all of the tags
        for tag_id in tag_ids:
            filters.append(Q(tags__in=tag_id))

    tables = Table.objects.filter(*filters)

    return tables


def listtables(request, schema_name: str):
    """
    :param request: A HTTP-request object sent by the Django framework
    :param schema_name: Name of a schema
    :return: Renders the list of all tables in the specified schema
    """

    if schema_name not in schema_whitelist or schema_name.startswith("_"):
        raise Http404("Schema not accessible")

    searched_query_string = request.GET.get("query")
    searched_tag_ids = request.GET.getlist("tags")

    Tag.increment_usage_count_many(searched_tag_ids)

    # find all tables (layzy query set) in this schema
    tables = find_tables(
        topic_name=schema_name,
        query_string=searched_query_string,
        tag_ids=searched_tag_ids,
    )

    tables = [
        (
            table.name,
            table.human_readable_name,
            [t.name for t in table.tags.order_by("-usage_count")],
        )
        for table in tables
    ]

    # sort by name
    tables = sorted(tables, key=lambda x: x[0])

    return render(
        request,
        "dataedit/dataedit_tablelist.html",
        {
            "schema": schema_name,
            "tables": tables,
            "query": searched_query_string,
            "tags": searched_tag_ids,
            "doc_oem_builder_link": DOCUMENTATION_LINKS["oemetabuilder"],
        },
    )


COMMENT_KEYS = [
    ("Title", "Title"),
    ("Description", "Description"),
    ("Reference Date", "Reference Date"),
    ("Spatial", "Spatial"),
    ("Temporal", "Temporal"),
    ("Source", "Source"),
    ("Licence", "Licence"),
    ("Contributors", "Contributors"),
    ("Fields", "Fields"),
]


def _type_json(json_obj):
    """
    Recursively labels JSON-objects by their types. Singleton lists are handled
    as elementary objects.

    :param json_obj: An JSON-object - possibly a dictionary, a list
        or an elementary JSON-object (e.g a string)

    :return: An annotated JSON-object (type, object)

    """
    if isinstance(json_obj, dict):
        return "dict", [(k, _type_json(json_obj[k])) for k in json_obj]
    elif isinstance(json_obj, list):
        if len(json_obj) == 1:
            return _type_json(json_obj[0])
        return "list", [_type_json(e) for e in json_obj]
    else:
        return str(type(json_obj)), json_obj


pending_dumps = {}


class RevisionView(View):
    def get(self, request, schema, table):
        return redirect(f"/api/v0/schema/{schema}/tables/{table}/rows")


def get_dependencies(schema, table, found=None):
    if not found:
        found = {(schema, table)}

    query = "SELECT DISTINCT \
        ccu.table_name AS foreign_table, \
        ccu.table_schema AS foreign_schema \
        FROM  \
        information_schema.table_constraints AS tc \
        JOIN information_schema.constraint_column_usage AS ccu \
          ON ccu.constraint_name = tc.constraint_name \
        WHERE constraint_type = 'FOREIGN KEY' AND tc.table_schema='{schema}'\
        AND tc.table_name='{table}';".format(
        schema=schema, table=table
    )

    engine = actions._get_engine()
    # metadata = sqla.MetaData(bind=engine)
    Session = sessionmaker()
    session = Session(bind=engine)

    result = session.execute(query)
    found_new = {
        (row.foreign_schema, row.foreign_table)
        for row in result
        if (row.foreign_schema, row.foreign_table) not in found
    }
    found = found.union(found_new)
    found.add((schema, table))
    session.close()
    for s, t in found_new:
        found = found.union(get_dependencies(s, t, found))

    return found


def create_dump(schema, table, fname):
    assert re.match(actions.pgsql_qualifier, table)
    assert re.match(actions.pgsql_qualifier, schema)
    for path in [
        "/dumps",
        "/dumps/{schema}".format(schema=schema),
        "/dumps/{schema}/{table}".format(schema=schema, table=table),
    ]:
        if not os.path.exists(sec.MEDIA_ROOT + path):
            os.mkdir(sec.MEDIA_ROOT + path)
    L = [
        "pg_dump",
        "-O",
        "-x",
        "-w",
        "-Fc",
        "--quote-all-identifiers",
        "-U",
        sec.dbuser,
        "-h",
        sec.dbhost,
        "-p",
        str(sec.dbport),
        "-d",
        sec.dbname,
        "-f",
        sec.MEDIA_ROOT
        + "/dumps/{schema}/{table}/".format(schema=schema, table=table)
        + fname
        + ".dump",
    ] + reduce(
        add,
        (["-n", s, "-t", s + "." + t] for s, t in get_dependencies(schema, table)),
        [],
    )
    return call(L, shell=False)


def send_dump(schema, table, fname):
    path = sec.MEDIA_ROOT + "/dumps/{schema}/{table}/{fname}.dump".format(
        fname=fname, schema=schema, table=table
    )
    f = FileWrapper(open(path, "rb"))
    response = HttpResponse(f, content_type="application/x-gzip")

    response["Content-Disposition"] = "attachment; filename=%s" % smart_str(
        "{schema}_{table}_{date}.tar.gz".format(date=fname, schema=schema, table=table)
    )

    # It's usually a good idea to set the 'Content-Length' header too.
    # You can also set any other required headers: Cache-Control, etc.
    return response


def show_revision(request, schema, table, date):
    # global pending_dumps

    rev = TableRevision.objects.get(schema=schema, table=table, date=date)
    rev.last_accessed = timezone.now()
    rev.save()
    return send_dump(schema, table, date)


@login_required
def tag_overview(request):
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
def tag_editor(request, id: str = ""):
    tag = Tag.objects.filter(pk=id).first()
    if tag:
        assigned = bool(tag.tables)
        return render(
            request=request,
            template_name="dataedit/tag_editor.html",
            context={
                "name": tag.name,
                "id": tag.pk,
                "color": tag.color,
                "assigned": assigned,
            },
        )
    else:
        return render(
            request=request,
            template_name="dataedit/tag_editor.html",
            context={"name": "", "color": "#000000", "assigned": False},
        )


@login_required
def change_tag(request):
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
        except sqla.exc.IntegrityError:
            # requested changes are not valid because of name conflicts
            status = "invalid"

    elif "submit_delete" in request.POST:
        id = request.POST["tag_id"]
        delete_tag(id)

    return redirect("/dataedit/tags/?status=" + status)


def edit_tag(id: str, name: str, color: str) -> None:
    """
    Args:
        id(int): tag id
        name(str): max 40 character tag text
        color(str): hexadecimal color code, eg #aaf0f0
    Raises:
        sqlalchemy.exc.IntegrityError if name is not ok

    """
    tag = Tag.objects.get(pk=id)
    tag.name = name
    tag.color = Tag.color_from_hex(color)
    tag.save()


def delete_tag(id: str) -> None:
    Tag.objects.get(pk=id).delete()


def add_tag(name: str, color: str) -> None:
    """
    Args:
        name(str): max 40 character tag text
        color(str): hexadecimal color code, eg #aaf0f0
    """
    Tag(name=name, color=Tag.color_from_hex(color)).save()


def view_save(request, schema, table):
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
            if item_name.startswith("y-axis-") and item_value == "on":
                y_axis_list.append(item_name["y-axis-".__len__() :])
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
        update_view.name = post_name
        update_view.options = post_options
    else:
        update_view = DBView(
            name=post_name,
            type=post_type,
            options=post_options,
            table=table,
            schema=schema,
        )

    update_view.save()

    # create and update filters
    post_filter_json = request.POST.get("filter")
    if post_filter_json != "":
        post_filter = json.loads(post_filter_json)

        for db_filter in update_view.filter.all():
            # look for filters in the database, that aren't used anymore and delete them
            db_filter_is_used = False
            for defined_filter in post_filter:
                if "id" in defined_filter:
                    if db_filter.id == defined_filter["id"]:
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

    return redirect("../../" + table + "?view=" + str(update_view.id))


def view_set_default(request, schema, table):
    post_id = request.GET.get("id")

    for view in DBView.objects.filter(schema=schema, table=table):
        if str(view.id) == post_id:
            view.is_default = True
        else:
            view.is_default = False
        view.save()
    return redirect("/dataedit/view/" + schema + "/" + table)


def view_delete(request, schema, table):
    post_id = request.GET.get("id")

    view = DBView.objects.get(id=post_id, schema=schema, table=table)
    view.delete()

    return redirect("/dataedit/view/" + schema + "/" + table)


class GraphView(View):
    def get(self, request, schema, table):
        # get the columns id from the schema and the table
        columns = [(c, c) for c in actions.describe_columns(schema, table).keys()]
        formset = GraphViewForm(columns=columns)

        return render(request, "dataedit/tablegraph_form.html", {"formset": formset})

    def post(self, request, schema, table):
        # save an instance of View, look at GraphViewForm fields in forms.py
        # for information to the options
        opt = dict(x=request.POST.get("column_x"), y=request.POST.get("column_y"))
        gview = DataViewModel.objects.create(
            name=request.POST.get("name"),
            table=table,
            schema=schema,
            type="graph",
            options=opt,
            is_default=request.POST.get("is_default", False),
        )
        gview.save()

        return redirect(
            "/dataedit/view/{schema}/{table}?view={view_id}".format(
                schema=schema, table=table, view_id=gview.id
            )
        )


class MapView(View):
    def get(self, request, schema, table, maptype):
        columns = [(c, c) for c in actions.describe_columns(schema, table).keys()]
        if maptype == "latlon":
            form = LatLonViewForm(columns=columns)
        elif maptype == "geom":
            form = GeomViewForm(columns=columns)
        else:
            raise Http404

        return render(request, "dataedit/tablemap_form.html", {"form": form})

    def post(self, request, schema, table, maptype):
        columns = [(c, c) for c in actions.describe_columns(schema, table).keys()]
        if maptype == "latlon":
            form = LatLonViewForm(request.POST, columns=columns)
            options = dict(lat=request.POST.get("lat"), lon=request.POST.get("lon"))
        elif maptype == "geom":
            form = GeomViewForm(request.POST, columns=columns)
            options = dict(geom=request.POST.get("geom"))
        else:
            raise Http404

        form.schema = schema
        form.table = table
        form.options = options
        if form.is_valid():
            view_id = form.save(commit=True)
            return redirect(
                "/dataedit/view/{schema}/{table}?view={view_id}".format(
                    schema=schema, table=table, view_id=view_id
                )
            )
        else:
            return self.get(request, schema, table)


class DataView(View):
    """This class handles the GET and POST requests for the main page of data edit.

    This view is displayed when a table is clicked on after choosing a schema
    on the website

    Initializes the session data (if necessary)
    """

    # TODO Check if this hits bad in performance
    @method_decorator(never_cache)
    def get(self, request, schema, table):
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

        if (
            schema not in schema_whitelist and schema != SCHEMA_DEFAULT_TEST_SANDBOX
        ) or schema.startswith("_"):
            raise Http404("Schema not accessible")

        metadata = load_metadata_from_db(schema, table)
        table_obj = Table.load(schema, table)
        if table_obj is None:
            raise Http404("Table object could not be loaded")

        # oemetadata = table_obj.oemetadata

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

        api_changes = change_requests(schema, table)
        data = api_changes.get("data")
        display_message = api_changes.get("display_message")
        display_items = api_changes.get("display_items")

        is_admin = False
        can_add = False
        if request.user and not request.user.is_anonymous:
            is_admin = request.user.has_admin_permissions(schema, table)
            level = request.user.get_table_permission_level(table_obj)
            can_add = level >= login_models.WRITE_PERM

        table_label = table_obj.human_readable_name

        table_views = DBView.objects.filter(table=table).filter(schema=schema)
        default = DBView(name="default", type="table", table=table, schema=schema)
        view_id = request.GET.get("view")

        embargo = Embargo.objects.filter(table=table_obj).first()
        if embargo:
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
        reviews = opr_manager.filter_opr_by_table(schema=schema, table=table)

        opr_context = {
            "contributor": PeerReviewManager.load_contributor(
                schema_name=schema, table_name=table
            ),
            "reviewer": PeerReviewManager.load_reviewer(schema=schema, table=table),
            "opr_enabled": False,
            # oemetadata
            # is not None,  # check if the table has the metadata
        }

        opr_result_context = {}
        if reviews.exists():
            latest_review = reviews.last()
            opr_manager.update_open_since(opr=latest_review)
            current_reviewer = opr_manager.load(latest_review).current_reviewer
            opr_context.update(
                {
                    "opr_id": latest_review.id,
                    "opr_current_reviewer": current_reviewer,
                    "is_finished": latest_review.is_finished,
                }
            )

            if latest_review.is_finished:
                badge = latest_review.review.get("badge")
                date_finished = latest_review.date_finished
                opr_result_context.update(
                    {
                        "badge": badge,
                        "review_url": None,
                        "date_finished": date_finished,
                        "review_id": latest_review.id,
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
            "schema": schema,
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

    def post(self, request, schema, table):
        """
        Handles the behaviour if a .csv-file is sent to the view of a table.
        The contained datasets are inserted into the corresponding table via
        the API.
        :param request: A HTTP-request object sent by the Django framework
        :param schema: Name of a schema
        :param table: Name of a table
        :return: Redirects to the view of the table the data was sent to.
        """
        if request.POST and request.FILES:
            csvfile = TextIOWrapper(
                request.FILES["csv_file"].file, encoding=request.encoding
            )

            reader = csv.DictReader(csvfile, delimiter=",")

            actions.data_insert(
                {
                    "schema": schema,
                    "table": table,
                    "method": "values",
                    "values": reader,
                },
                {"user": request.user},
            )
        return redirect(
            "/dataedit/view/{schema}/{table}".format(schema=schema, table=table)
        )


class PermissionView(View):
    """This method handles the GET requests for the main page of data edit.
    Initialises the session data (if necessary)
    """

    def get(self, request, schema, table):
        if schema not in schema_whitelist:
            raise Http404("Schema not accessible")

        table_obj = Table.load(schema, table)

        user_perms = login_models.UserPermission.objects.filter(table=table_obj)
        group_perms = login_models.GroupPermission.objects.filter(table=table_obj)
        is_admin = False
        can_add = False
        can_remove = False
        level = login_models.NO_PERM
        if not request.user.is_anonymous:
            level = request.user.get_table_permission_level(table_obj)
            is_admin = level >= login_models.ADMIN_PERM
            can_add = level >= login_models.WRITE_PERM
            can_remove = level >= login_models.DELETE_PERM
        return render(
            request,
            "dataedit/table_permissions.html",
            {
                "table": table,
                "schema": schema,
                "user_perms": user_perms,
                "group_perms": group_perms,
                "choices": login_models.TablePermission.choices,
                "can_add": can_add,
                "can_remove": can_remove,
                "is_admin": is_admin,
                "own_level": level,
            },
        )

    def post(self, request, schema, table):
        table_obj = Table.load(schema, table)
        if (
            request.user.is_anonymous
            or request.user.get_table_permission_level(table_obj)
            < login_models.ADMIN_PERM
        ):
            raise PermissionDenied
        if request.POST["mode"] == "add_user":
            return self.__add_user(request, schema, table)
        if request.POST["mode"] == "alter_user":
            return self.__change_user(request, schema, table)
        if request.POST["mode"] == "remove_user":
            return self.__remove_user(request, schema, table)
        if request.POST["mode"] == "add_group":
            return self.__add_group(request, schema, table)
        if request.POST["mode"] == "alter_group":
            return self.__change_group(request, schema, table)
        if request.POST["mode"] == "remove_group":
            return self.__remove_group(request, schema, table)

    def __add_user(self, request, schema, table):
        user_name = request.POST.get("name")
        # Check if the user name is empty
        if not user_name:
            # Return an HTTP 400 Bad Request response
            return HttpResponseBadRequest("User name is required.")

        user = login_models.myuser.objects.filter(name=user_name).first()
        table_obj = Table.load(schema, table)
        p, _ = login_models.UserPermission.objects.get_or_create(
            holder=user, table=table_obj
        )
        p.save()
        return self.get(request, schema, table)

    def __change_user(self, request, schema, table):
        user_id = request.POST.get("user_id")
        # Check if the user id is empty
        if not user_id:
            # Return an HTTP 400 Bad Request response
            return HttpResponseBadRequest("User id is required.")

        user = login_models.myuser.objects.filter(id=user_id).first()
        table_obj = Table.load(schema, table)
        p = get_object_or_404(login_models.UserPermission, holder=user, table=table_obj)
        p.level = request.POST["level"]
        p.save()
        return self.get(request, schema, table)

    def __remove_user(self, request, schema, table):
        user_id = request.POST.get("user_id")
        # Check if the user id is empty
        if not user_id:
            # Return an HTTP 400 Bad Request response
            return HttpResponseBadRequest("User id is required.")

        user = get_object_or_404(login_models.myuser, id=user_id)
        table_obj = Table.load(schema, table)
        p = get_object_or_404(login_models.UserPermission, holder=user, table=table_obj)
        p.delete()
        return self.get(request, schema, table)

    def __add_group(self, request, schema, table):
        group_name = request.POST.get("name")
        # Check if the group name is empty
        if not group_name:
            # Return an HTTP 400 Bad Request response
            return HttpResponseBadRequest("Group name is required.")

        group = get_object_or_404(login_models.UserGroup, name=group_name)
        table_obj = Table.load(schema, table)
        p, _ = login_models.GroupPermission.objects.get_or_create(
            holder=group, table=table_obj
        )
        p.save()
        return self.get(request, schema, table)

    def __change_group(self, request, schema, table):
        group_id = request.POST.get("group_id")
        if not group_id:
            # Return an HTTP 400 Bad Request response
            return HttpResponseBadRequest("Group id is required.")

        group = get_object_or_404(login_models.UserGroup, id=group_id)
        table_obj = Table.load(schema, table)
        p = get_object_or_404(
            login_models.GroupPermission, holder=group, table=table_obj
        )
        p.level = request.POST["level"]
        p.save()
        return self.get(request, schema, table)

    def __remove_group(self, request, schema, table):
        group_id = request.POST.get("group_id")
        if not group_id:
            # Return an HTTP 400 Bad Request response
            return HttpResponseBadRequest("Group id is required.")

        group = get_object_or_404(login_models.UserGroup, id=group_id)
        table_obj = Table.load(schema, table)
        p = get_object_or_404(
            login_models.GroupPermission, holder=group, table=table_obj
        )
        p.delete()
        return self.get(request, schema, table)


def update_tags_from_keywords(table_name: str, keywords: list[str]) -> list[str]:
    table = Table.objects.get(name=table_name)
    table.tags.clear()
    keywords_new = set()
    for keyword in keywords:
        tag = Tag.get_or_create_from_name(keyword)
        table.tags.add(tag)
        keywords_new.add(tag.name_normalized)
    table.save()
    return list(keywords_new)


def update_keywords_from_tags(table: Table, schema_name: str) -> None:
    """synchronize keywords in metadata with tags"""

    metadata = table.oemetadata or {"resources": [{}]}
    keywords = [tag.name_normalized for tag in table.tags.all()]
    metadata["resources"][0]["keywords"] = keywords

    actions.set_table_metadata(
        table_name=table.name, schema_name=schema_name, metadata=metadata
    )


@login_required
def update_table_tags(request):
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
    # check if valid table / schema
    schema_name, table_name = actions.get_table_name(
        schema=request.POST["schema"],
        table=request.POST["table"],
        restrict_schemas=False,
    )
    # check write permission
    actions.assert_add_tag_permission(
        request.user, table_name, login_models.WRITE_PERM, schema=schema_name
    )

    tag_ids = {
        field[len("tag_") :] for field in request.POST if field.startswith("tag_")
    }
    tags = Tag.objects.filter(pk__in=tag_ids)
    table = Table.objects.get(name=table_name)
    table.tags.clear()
    for tag in tags:
        table.tags.add(tag)
    table.save()  # TODO: we already do save in update_keywords_from_tags further down

    update_keywords_from_tags(table, schema_name=schema_name)

    message = messages.success(
        request,
        'Please note that OEMetadata keywords and table tags are synchronized. When submitting new tags, you may notice automatic changes to the table tags on the OEP and/or the "Keywords" field in the metadata.',  # noqa
        # noqa
    )

    return render(
        request,
        "dataedit/dataview.html",
        {"messages": message, "table": table_name, "schema": schema_name},
    )


def redirect_after_table_tags_updated(request):
    update_table_tags(request)
    return redirect(request.META["HTTP_REFERER"])


def get_all_tags(
    schema_name: str | None = None, table_name: str | None = None
) -> list[dict]:
    """
    Load all tags of a specific table
    :param schema: Name of a schema
    :param table: Name of a table
    :return:
    """
    tags: Iterable[Tag]
    if table_name:
        tags = Table.objects.get(name=table_name).tags.all()
    else:
        tags = Tag.objects.all()

    tag_dicts = [
        {
            "id": tag.pk,
            "name": tag.name,
            "name_normalized": tag.name_normalized,
            "color": tag.color_hex,
            "usage_count": tag.usage_count,
            "usage_tracked_since": tag.usage_tracked_since,
        }
        for tag in tags
    ]
    return sort_tags_by_popularity(tag_dicts)


def sort_tags_by_popularity(tags):
    def key_func(tag):
        # track_time = tag["usage_tracked_since"] - datetime.datetime.utcnow()
        return tag["usage_count"]

    tags.sort(reverse=True, key=key_func)
    return tags


def get_popular_tags(
    schema_name: str | None = None, table_name: str | None = None, limit=10
):
    tags = get_all_tags(table_name=table_name)
    sort_tags_by_popularity(tags)

    return tags[:limit]


def get_column_description(schema, table):
    """Return list of column descriptions:
    [{
       "name": str,
       "data_type": str,
       "is_nullable': bool,
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

    _columns = actions.describe_columns(schema, table)
    _constraints = actions.describe_constraints(schema, table)
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


class WizardView(LoginRequiredMixin, View):
    """View for the upload wizard (create tables, upload csv)."""

    def get(self, request, schema=SCHEMA_DATA, table=None):
        """Handle GET request (render the page)."""
        engine = actions._get_engine()
        schema = utils.validate_schema(schema)

        can_add = False
        columns = None
        # pk_fields = None
        n_rows = None
        if table:
            # get information about the table
            # if upload: table must exist in schema model_draft
            if not engine.dialect.has_table(engine, table, schema=schema):
                raise Http404("Table does not exist")
            table_obj = Table.load(schema, table)
            if not request.user.is_anonymous:
                # user_perms = login_models.UserPermission.objects.filter(table=table_obj)  # noqa
                level = request.user.get_table_permission_level(table_obj)
                can_add = level >= login_models.WRITE_PERM
            columns = get_column_description(schema, table)
            # get number of rows
            sql = "SELECT COUNT(*) FROM {schema}.{table}".format(
                schema=schema, table=table
            )
            res = actions.perform_sql(sql)
            n_rows = res["result"].fetchone()[0]

        context = {
            "config": json.dumps(
                {  # pass as json string
                    "canAdd": can_add,
                    "columns": columns,
                    "schema": schema,
                    "table": table,
                    "nRows": n_rows,
                }
            ),
            "schema": schema,
            "table": table,
            "can_add": can_add,
            "wizard_academy_link": EXTERNAL_URLS["tutorials_wizard"],
            "create_database_conform_data": EXTERNAL_URLS[
                "tutorials_create_database_conform_data"
            ],
        }

        return render(request, "dataedit/wizard.html", context=context)


def get_cancle_state(request):
    return request.META.get("HTTP_REFERER")


class MetaEditView(LoginRequiredMixin, View):
    """Metadata editor (cliet side json forms)."""

    def get(self, request, schema, table):
        columns = get_column_description(schema, table)

        can_add = False
        table_obj = Table.load(schema, table)
        if not request.user.is_anonymous:
            level = request.user.get_table_permission_level(table_obj)
            can_add = level >= login_models.WRITE_PERM

        url_table_id = request.build_absolute_uri(
            reverse("dataedit:view", kwargs={"schema": schema, "table": table})
        )

        context_dict = {
            "schema": schema,
            "table": table,
            "config": json.dumps(
                {
                    "schema": schema,
                    "table": table,
                    "columns": columns,
                    "url_table_id": url_table_id,
                    "url_api_meta": reverse(
                        "api:api_table_meta", kwargs={"schema": schema, "table": table}
                    ),
                    "url_view_table": reverse(
                        "dataedit:view", kwargs={"schema": schema, "table": table}
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


class StandaloneMetaEditView(View):
    def get(self, request):
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


class PeerReviewView(LoginRequiredMixin, View):
    """
    A view handling the peer review of metadata. This view supports loading,
    parsing, sorting metadata, and handling GET and POST requests for peer review.
    """

    def load_json(self, schema, table, review_id=None):
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
            metadata = load_metadata_from_db(schema, table)
        elif review_id:
            opr = PeerReviewManager.filter_opr_by_id(opr_id=review_id)
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
                # pass
            else:
                for i, k in enumerate(val):
                    lines += self.parse_keys(
                        k, old + "." + str(i)
                    )  # handles user value
        else:
            lines += [{"field": old[1:], "value": str(val)}]
        return lines

    def sort_in_category(self, schema, table, oemetadata):
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
        import re
        from collections import defaultdict

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

    def get(self, request, schema, table, review_id=None):
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
        # review_state = PeerReview.is_finished  # TODO: Use later
        json_schema = self.load_json_schema()
        can_add = False
        table_obj = Table.load(schema, table)
        field_descriptions = self.get_all_field_descriptions(json_schema)

        # Check user permissions
        if not request.user.is_anonymous:
            level = request.user.get_table_permission_level(table_obj)
            can_add = level >= login_models.WRITE_PERM

        oemetadata = self.load_json(schema, table, review_id)
        metadata = self.sort_in_category(
            schema, table, oemetadata=oemetadata
        )  # Generate URL for peer_review_reviewer
        if review_id is not None:
            url_peer_review = reverse(
                "dataedit:peer_review_reviewer",
                kwargs={"schema": schema, "table": table, "review_id": review_id},
            )
            opr_review = PeerReviewManager.filter_opr_by_id(opr_id=review_id)
            existing_review = opr_review.review.get("reviews", [])
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
                "dataedit:peer_review_create", kwargs={"schema": schema, "table": table}
            )
            # existing_review={}
            state_dict = None
            review_finished = None

        config_data = {
            "can_add": can_add,
            "url_peer_review": url_peer_review,
            "url_table": reverse(
                "dataedit:view", kwargs={"schema": schema, "table": table}
            ),
            "topic": schema,
            "table": table,
            "review_finished": review_finished,
            "review_id": review_id,
        }
        context_meta = {
            # need this here as json.dumps breaks the template syntax access
            # like {{ config.table }} now you can use {{ table }}
            "table": table,
            "topic": schema,
            "config": json.dumps(config_data),
            "meta": metadata,
            "json_schema": json_schema,
            "field_descriptions_json": json.dumps(field_descriptions),
            "state_dict": json.dumps(state_dict),
            "review_finished": review_finished,
            "review_id": review_id,
        }
        return render(request, "dataedit/opr_review.html", context=context_meta)

    def post(self, request, schema_name: str, table_name: str, review_id=None):
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
        context = {}
        if request.method == "POST":
            # get the review data and additional application metadata
            # from user peer review submit/save
            review_data = json.loads(request.body)
            if review_id:
                contributor_review = PeerReview.objects.filter(id=review_id).first()
                if contributor_review:
                    contributor_review_data = contributor_review.review.get(
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

            contributor = PeerReviewManager.load_contributor(schema_name, table_name)

            if contributor is not None:
                # Überprüfen, ob ein aktiver PeerReview existiert
                active_peer_review = PeerReview.load(
                    schema=schema_name, table=table_name
                )
                if active_peer_review is None or active_peer_review.is_finished:
                    # Kein aktiver PeerReview vorhanden
                    # oder der aktive PeerReview ist abgeschlossen
                    table_review = PeerReview(
                        schema=schema_name,
                        table=table_name,
                        is_finished=review_finished,
                        review=review_datamodel,
                        reviewer=request.user,
                        contributor=contributor,
                        oemetadata=load_metadata_from_db(
                            schema_name=schema_name, table_name=table_name
                        ),
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
                    active_peer_review.reviewer = request.user
                    active_peer_review.contributor = contributor
                    active_peer_review.update(review_type=review_post_type)
            else:
                error_msg = (
                    "Failed to retrieve any user that identifies "
                    f"as table holder for the current table: {table_name}!"
                )
                return JsonResponse({"error": error_msg}, status=400)

            # TODO: Check for schema/topic as reviewed finished also indicates the table
            # needs to be or has to be moved.
            if review_finished is True:
                review_table = Table.load(
                    schema_name=schema_name, table_name=table_name
                )
                review_table.set_is_reviewed()
                metadata = self.load_json(schema_name, table_name, review_id=review_id)
                updated_metadata = recursive_update(metadata, review_data)
                save_metadata_to_db(schema_name, table_name, updated_metadata)
                active_peer_review = PeerReview.load(
                    schema=schema_name, table=table_name
                )

                if active_peer_review:
                    updated_oemetadata = recursive_update(
                        active_peer_review.oemetadata, review_data
                    )
                    active_peer_review.oemetadata = updated_oemetadata
                    active_peer_review.save()

                # TODO: also update reviewFinished in review datamodel json
                # logging.INFO(f"Table {table.name} is now reviewed and can be moved
                # to the destination schema.")

        return render(request, "dataedit/opr_review.html", context=context)


class PeerRreviewContributorView(PeerReviewView):
    """
    A view handling the contributor's side of the peer review process.
    This view supports rendering the review template and handling GET and
    POST requests for contributor's review.
    """

    def get(self, request, schema, table, review_id):
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
        can_add = False
        peer_review = PeerReview.objects.get(id=review_id)
        table_obj = Table.load(peer_review.schema, peer_review.table)
        if not request.user.is_anonymous:
            level = request.user.get_table_permission_level(table_obj)
            can_add = level >= login_models.WRITE_PERM
        oemetadata = self.load_json(schema, table, review_id)
        metadata = self.sort_in_category(schema, table, oemetadata=oemetadata)
        json_schema = self.load_json_schema()
        field_descriptions = self.get_all_field_descriptions(json_schema)
        review_data = peer_review.review.get("reviews", [])

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
                            "schema": schema,
                            "table": table,
                            "review_id": review_id,
                        },
                    ),
                    "url_table": reverse(
                        "dataedit:view", kwargs={"schema": schema, "table": table}
                    ),
                    "topic": schema,
                    "table": table,
                }
            ),
            "table": table,
            "topic": schema,
            "meta": metadata,
            "json_schema": json_schema,
            "field_descriptions_json": json.dumps(field_descriptions),
            "state_dict": json.dumps(state_dict),
        }
        return render(request, "dataedit/opr_contributor.html", context=context_meta)

    def post(self, request, schema, table, review_id):
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

        context = {}
        if request.method == "POST":
            review_data = json.loads(request.body)
            review_post_type = review_data.get("reviewType")
            review_datamodel = review_data.get("reviewData")
            # unused
            # review_state = review_data.get("reviewFinished")
            current_opr = PeerReviewManager.filter_opr_by_id(opr_id=review_id)
            existing_reviews = current_opr.review
            merged_review = merge_field_reviews(
                current_json=existing_reviews, new_json=review_datamodel
            )

            current_opr.review = merged_review
            current_opr.update(review_type=review_post_type)

        return render(request, "dataedit/opr_contributor.html", context=context)


def metadata_widget(request):
    """
    A view to render the metadata widget for the dataedit app.
    The metadata widget is a small widget that can be embedded in other
    applications to display metadata information.

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        HttpResponse: Rendered HTML response for the metadata widget.
    """
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
    # context = {"meta": OEMETADATA_V20_EXAMPLE}

    return render(request, "partials/metadata_viewer.html", context=context)
