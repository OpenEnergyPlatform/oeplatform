import csv
import json
import logging
import os
import re
from functools import reduce
from io import TextIOWrapper
from itertools import chain
from operator import add
from subprocess import call
from wsgiref.util import FileWrapper

import sqlalchemy as sqla
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.search import SearchQuery
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import smart_str
from django.views.decorators.cache import never_cache
from django.views.generic import View
from metadata.v160.schema import OEMETADATA_V160_SCHEMA
from metadata.v160.template import OEMETADATA_V160_TEMPLATE
from sqlalchemy.dialects.postgresql import array_agg
from sqlalchemy.orm import sessionmaker

import api.parser
from api.actions import describe_columns

try:
    import oeplatform.securitysettings as sec
except Exception:
    logging.error("No securitysettings found. Triggerd in dataedit/views.py")

from django.contrib import messages

from api import actions as actions
from api.connection import _get_engine, create_oedb_session
from dataedit.forms import GeomViewForm, GraphViewForm, LatLonViewForm
from dataedit.helper import merge_field_reviews, process_review_data, recursive_update
from dataedit.metadata import load_metadata_from_db, save_metadata_to_db
from dataedit.metadata.widget import MetaDataWidget
from dataedit.models import Embargo
from dataedit.models import Filter as DBFilter
from dataedit.models import PeerReview, PeerReviewManager, Table
from dataedit.models import View as DBView
from dataedit.structures import TableTags, Tag
from login import models as login_models
from oeplatform.settings import DOCUMENTATION_LINKS, EXTERNAL_URLS

from .models import TableRevision
from .models import View as DataViewModel

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
]

schema_sandbox = "sandbox"


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

    try:
        searched_tag_ids = list(
            map(
                lambda t: int(t),
                request.GET.getlist("tags"),
            )
        )
    except ValueError:
        raise Http404

    for tag_id in searched_tag_ids:
        increment_usage_count(tag_id)

    # find all tables (layzy query set)
    tables = find_tables(query_string=searched_query_string, tag_ids=searched_tag_ids)

    # get table count per schema
    response = tables.values("schema__name").annotate(tables_count=Count("name"))

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

    schemas = [
        (
            row["schema__name"],
            description.get(row["schema__name"], "No description"),
            row["tables_count"],  # number of tables in schema
        )
        for row in response
    ]

    # sort by name
    schemas = sorted(schemas, key=lambda x: x[0])
    return render(
        request,
        "dataedit/dataedit_schemalist.html",
        {
            "schemas": schemas,
            "query": searched_query_string,
            "tags": searched_tag_ids,
            "doc_oem_builder_link": DOCUMENTATION_LINKS["oemetabuilder"],
        },
    )


def get_session_query():
    engine = actions._get_engine()
    conn = engine.connect()
    Session = sessionmaker()
    session = Session(bind=conn)
    return session.query


def find_tables(schema_name=None, query_string=None, tag_ids=None):
    """find tables given search criteria

    Args:
        schema_name (str, optional): only tables in this schema
        query_string (str, optional): user search term
        tag_ids (list, optional): list of tag ids

    Returns:
        QuerySet of Table objetcs
    """

    # define search filter (will be combined with AND):
    filters = []

    # only whitelisted schemata:
    filters.append(Q(schema__name__in=schema_whitelist))

    if schema_name:  # only tables in schema
        filters.append(Q(schema__name=schema_name))

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
        filter_tags = [TableTags.tag.in_(tag_ids)]
        if schema_name:
            filter_tags.append(TableTags.schema_name == schema_name)

        tag_query = (
            get_session_query()(
                TableTags.schema_name,
                TableTags.table_name,
            )
            .filter(*filter_tags)
            .group_by(TableTags.schema_name, TableTags.table_name)
            .having(
                # only if number of matches == number of tags
                sqla.func.count()
                == len(tag_ids)
            )
        )

        filter_tables = Q(pk__in=[])
        # start with a "always false" condition, because we add OR statements
        # see: https://forum.djangoproject.com/t/improving-q-objects-with-true-false-and-none/851   # noqa

        for schema_name, table_name in tag_query:
            filter_tables = filter_tables | (
                Q(schema__name=schema_name) & Q(name=table_name)
            )

        filters.append(filter_tables)

    tables = Table.objects.filter(*filters)

    return tables


def listtables(request, schema_name):
    """
    :param request: A HTTP-request object sent by the Django framework
    :param schema_name: Name of a schema
    :return: Renders the list of all tables in the specified schema
    """

    if schema_name not in schema_whitelist or schema_name.startswith("_"):
        raise Http404("Schema not accessible")

    searched_query_string = request.GET.get("query")
    searched_tag_ids = list(
        map(
            int,
            request.GET.getlist("tags"),
        )
    )

    for tag_id in searched_tag_ids:
        increment_usage_count(tag_id)

    # find all tables (layzy query set) in this schema
    tables = find_tables(
        schema_name=schema_name,
        query_string=searched_query_string,
        tag_ids=searched_tag_ids,
    )

    # get all tags for table in schema
    tag_query = (
        get_session_query()(
            TableTags.table_name,
            array_agg(TableTags.tag),
            array_agg(Tag.name),
            array_agg(Tag.color),
            array_agg(Tag.usage_count),
        )
        .filter(TableTags.schema_name == schema_name, TableTags.tag == Tag.id)  # join
        .group_by(TableTags.table_name)
    )

    def create_taglist(row):
        return [
            dict(id=ident, name=label, color="#" + format(color, "06X"), popularity=pop)
            for ident, label, color, pop in zip(row[1], row[2], row[3], row[4])
        ]

    # group tags by table_name, order by popularity
    tags = {
        r[0]: sorted(create_taglist(r), key=lambda x: x["popularity"])
        for r in tag_query
    }

    tables = [
        (
            table.name,
            table.human_readable_name,
            tags.get(table.name, []),
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
    global pending_dumps

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
def tag_editor(request, id=""):
    tags = get_all_tags()

    # create_new = True

    for t in tags:
        if id != "" and int(id) == t["id"]:
            tag = t

            # inform the user if tag is assigned to an object
            engine = actions._get_engine()
            Session = sessionmaker()
            session = Session(bind=engine)
            assigned = (
                session.query(TableTags).filter(TableTags.tag == t["id"]).count() > 0
            )

            return render(
                request=request,
                template_name="dataedit/tag_editor.html",
                context={
                    "name": tag["name"],
                    "id": tag["id"],
                    "color": tag["color"],
                    "assigned": assigned,
                },
            )
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


def edit_tag(id, name, color):
    """
    Args:
        id(int): tag id
        name(str): max 40 character tag text
        color(str): hexadecimal color code, eg #aaf0f0
    Raises:
        sqlalchemy.exc.IntegrityError if name is not ok

    """
    engine = actions._get_engine()
    Session = sessionmaker()
    session = Session(bind=engine)

    result = session.query(Tag).filter(Tag.id == id).one()

    result.name = name
    result.name_normalized = Tag.create_name_normalized(name)
    result.color = str(int(color[1:], 16))
    session.commit()


def delete_tag(id):
    engine = actions._get_engine()
    Session = sessionmaker()
    session = Session(bind=engine)

    # delete all occurrences of the tag from Table_tag
    session.query(TableTags).filter(TableTags.tag == id).delete()

    # delete the tag from Tag
    session.query(Tag).filter(Tag.id == id).delete()

    session.commit()


def add_tag(name, color):
    """
    Args:
        name(str): max 40 character tag text
        color(str): hexadecimal color code, eg #aaf0f0
    Raises:
        sqlalchemy.exc.IntegrityError if name is not ok

    """
    engine = actions._get_engine()
    Session = sessionmaker()
    session = Session(bind=engine)

    session.add(Tag(**{"name": name, "color": str(int(color[1:], 16)), "id": None}))
    session.commit()


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
        columns = [(c, c) for c in describe_columns(schema, table).keys()]
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
        columns = [(c, c) for c in describe_columns(schema, table).keys()]
        if maptype == "latlon":
            form = LatLonViewForm(columns=columns)
        elif maptype == "geom":
            form = GeomViewForm(columns=columns)
        else:
            raise Http404

        return render(request, "dataedit/tablemap_form.html", {"form": form})

    def post(self, request, schema, table, maptype):
        columns = [(c, c) for c in describe_columns(schema, table).keys()]
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
    @never_cache
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
            schema not in schema_whitelist and schema != schema_sandbox
        ) or schema.startswith("_"):
            raise Http404("Schema not accessible")

        engine = actions._get_engine()

        if not engine.dialect.has_table(engine, table, schema=schema):
            raise Http404("Table does not exist in the database")

        actions.create_meta(schema, table)
        metadata = load_metadata_from_db(schema, table)
        table_obj = Table.load(schema, table)
        if table_obj is None:
            raise Http404("Table object could not be loaded")

        oemetadata = table_obj.oemetadata

        from dataedit.metadata import TEMPLATE_V1_5

        def iter_oem_key_order(metadata: dict):
            oem_151_key_order = [key for key in TEMPLATE_V1_5.keys()]
            for key in oem_151_key_order:
                yield key, metadata.get(key)

        ordered_oem_151 = {key: value for key, value in iter_oem_key_order(metadata)}
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
        else:
            try:
                # at first, try to use the view, that is passed as get argument
                current_view = table_views.get(id=view_id)
            except ObjectDoesNotExist:
                current_view = default

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
                schema=schema, table=table
            ),
            "reviewer": PeerReviewManager.load_reviewer(schema=schema, table=table),
            "opr_enabled": oemetadata
            is not None,  # check if the table has the metadata
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


def check_is_table_tag(session, schema, table, tag_id):
    """
    Check if a tag is existing in the table_tag table in schema public.
    Tags are queried by tag id.

    Args:
        session (sqlachemy): sqlachemy session
        tag_id (int): Tag ID

    Returns:
        bool: True if exists, False if not
    """

    t = session.query(TableTags.tag).filter_by(
        tag=tag_id, table_name=table, schema_name=schema
    )
    session.commit()
    return session.query(t.exists()).scalar()


def check_is_tag(session, tag_id):
    """
    Check if a tag is existing in the tag table in schema public.
    Tags are queried by tag_id.

    Args:
        session (sqlalchemy): Sqlalchemy session
        tag_id (int): [description]

    Returns:
        bool: True if exists, False if not
    """

    t = session.query(Tag).filter(Tag.id == tag_id)
    session.commit()
    return session.query(t.exists()).scalar()


def get_tag_id_by_tag_name_normalized(session, name_normalized):
    """
    Query the Tag table in schema public to get the Tag ID.
    Tags are queried by unique field tag_name_normalized.

    Args:
        session ([type]): [description]
        name_normalized ([type]): [description]

    Returns:
        int: Tag ID
        None: If Tag ID does not exists.

    """

    tag = session.query(Tag).filter(Tag.name_normalized == name_normalized).first()
    if tag is not None:
        return tag.id
    else:
        return None


def get_tag_name_normalized_by_id(session, tag_id):
    """
    Query the Tag table in schema public to get the tag_name_normalized.
    Tags are queried by tag id.

    Args:
        session (sqlachemy): sqlalachemy session
        tag_id (int): The Tag ID

    Returns:
        None: If tag id does not exists.
        Str: Tag name normalized
    """

    tag = session.query(Tag).filter(Tag.id == tag_id).first()
    session.commit()
    if tag is not None:
        return tag.name_normalized
    else:
        return None


def get_tag_name_by_id(session, tag_id):
    """
    Query the Tag table in schema public to get the tags.name.
    Tags are queried by tag id.

    Args:
        session (sqlachemy): sqlalachemy session
        tag_id (int): The Tag ID

    Returns:
        None: If tag id does not exists.
        Str: Tag name
    """

    tag = session.query(Tag).filter(Tag.id == tag_id).first()
    session.commit()
    if tag is not None:
        return tag.name
    else:
        return None


def add_existing_keyword_tag_to_table_tags(session, schema, table, keyword_tag_id):
    """
    Add a tag from the oem-keywords to the table_tags for the current table.

    Args:
        session (sqlachemy): sqlalachemy session
        schema (str): Name of the schema
        table (str): Name of the table
        keyword_tag_id (int): The tag id that machtes to keyword tag name
            (by tag_name_normalized)

    Returns:
        any: Exception
    """

    if check_is_tag(session, keyword_tag_id):
        t = TableTags(
            **{"schema_name": schema, "table_name": table, "tag": keyword_tag_id}
        )

        try:
            session.add(t)
            session.commit()
        except Exception as e:
            session.rollback()  # Rollback the changes on error
            return e
        finally:
            session.close()  # Close the connection


def get_tag_keywords_synchronized_metadata(
    table, schema, keywords_new=None, tag_ids_new=None
):
    """synchronize tags and keywords, either by new metadata OR by set of tag ids
    (from UI)

    Args:
        table (_type_): _description_
        schema (_type_): _description_
        metadata_new (_type_, optional): _description_. Defaults to None.
        tag_ids_new (_type_, optional): _description_. Defaults to None.
    """

    session = create_oedb_session()

    metadata = load_metadata_from_db(schema=schema, table=table)
    keywords_old = set(
        k for k in metadata.get("keywords", []) if Tag.create_name_normalized(k)
    )  # remove empy

    tag_ids_old = set(
        tt.tag
        for tt in session.query(TableTags).filter(
            TableTags.table_name == table, TableTags.schema_name == schema
        )
    )
    tags_old = session.query(Tag).filter(Tag.id.in_(tag_ids_old)).all()

    tags_by_name_normalized = {}
    tags_by_id = dict()

    for tag in tags_old:
        tags_by_name_normalized[tag.name_normalized] = tag
        tags_by_id[tag.id] = tag

    def get_or_create_tag_by_name(name):
        name_normalized = Tag.create_name_normalized(name)
        if not name_normalized:
            return None
        if name_normalized not in tags_by_name_normalized:
            tag = (
                session.query(Tag)
                .filter(Tag.name_normalized == name_normalized)
                .first()
            )
            if tag is None:
                name = name[:40]  # max len
                tag = Tag(name=name)
                session.add(tag)
                session.flush()
            assert tag.id
            tags_by_name_normalized[name_normalized] = tag
            tags_by_id[tag.id] = tag
        return tags_by_name_normalized[name_normalized]

    def get_tag_by_id(tag_id):
        if tag_id not in tags_by_id:
            tag = session.query(Tag).filter(Tag.id == tag_id).first()
            tags_by_name_normalized[tag.name_normalized] = tag
            tags_by_id[tag.id] = tag
        return tags_by_id[tag_id]

    # map old keywords to tag ids (create tags if needed)
    keyword_tag_ids_old = set(get_or_create_tag_by_name(n).id for n in keywords_old)

    if keywords_new is not None:  # user updated metadata keywords
        # map new keywords to tag ids (create tags if needed)
        keywords_new = [
            k for k in keywords_new if Tag.create_name_normalized(k)
        ]  # remove empy
        keyword_new_tag_ids = set(get_or_create_tag_by_name(n).id for n in keywords_new)

        # determine which tag ids the user wants to remove
        remove_table_tag_ids = keyword_tag_ids_old - keyword_new_tag_ids
        keyword_add_tag_ids = tag_ids_old - remove_table_tag_ids - keyword_new_tag_ids
        tag_ids_new = set()

    elif tag_ids_new is not None:  # user updated tags in UI
        # determine which tag ids the user wants to remove
        remove_table_tag_ids = tag_ids_old - tag_ids_new
        keywords_new = [
            k
            for k in keywords_old
            if get_or_create_tag_by_name(k).id not in remove_table_tag_ids
        ]
        keyword_new_tag_ids = set()
        keyword_add_tag_ids = tag_ids_new - keyword_tag_ids_old - remove_table_tag_ids

    else:
        raise NotImplementedError("must provide either metadata or tag_ids")

    # determine which tag ids have to be removed
    delete_table_tag_ids = remove_table_tag_ids & tag_ids_old
    for tid in delete_table_tag_ids:
        if tid is None:
            continue
        session.query(TableTags).filter(
            TableTags.table_name == table,
            TableTags.schema_name == schema,
            TableTags.tag == tid,
        ).delete()

    # determine which tag ids must be added
    add_table_tag_ids = (keyword_tag_ids_old | keyword_new_tag_ids | tag_ids_new) - (
        tag_ids_old | remove_table_tag_ids
    )
    for tid in add_table_tag_ids:
        if tid is None:
            continue
        session.add(TableTags(table_name=table, schema_name=schema, tag=tid))

    # determine wich keywords need to be added
    for tid in keyword_add_tag_ids:
        if tid is None:
            continue
        keywords_new.append(get_tag_by_id(tid).name)

    session.commit()
    session.close()

    metadata["keywords"] = keywords_new

    return metadata


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
    schema, table = actions.get_table_name(
        schema=request.POST["schema"],
        table=request.POST["table"],
        restrict_schemas=False,
    )
    # check write permission
    actions.assert_add_tag_permission(
        request.user, table, login_models.WRITE_PERM, schema=schema
    )

    ids = {
        int(field[len("tag_") :]) for field in request.POST if field.startswith("tag_")
    }

    with _get_engine().connect() as con:
        with con.begin():
            if not actions.assert_has_metadata(table=table, schema=schema):
                actions.set_table_metadata(
                    table=table,
                    schema=schema,
                    metadata=OEMETADATA_V160_TEMPLATE,
                    cursor=con,
                )
                # update tags in db and harmonize metadata

            metadata = get_tag_keywords_synchronized_metadata(
                table=table, schema=schema, tag_ids_new=ids
            )

            # TODO Add metadata to table (JSONB field) somewhere here
            actions.set_table_metadata(
                table=table, schema=schema, metadata=metadata, cursor=con
            )

    message = messages.success(
        request,
        'Please note that OEMetadata keywords and table tags are synchronized. When submitting new tags, you may notice automatic changes to the table tags on the OEP and/or the "Keywords" field in the metadata.',  # noqa
        # noqa
    )

    return render(
        request,
        "dataedit/dataview.html",
        {"messages": message, "table": table, "schema": schema},
    )


def redirect_after_table_tags_updated(request):
    update_table_tags(request)
    return redirect(request.META["HTTP_REFERER"])


def get_all_tags(schema=None, table=None):
    """
    Load all tags of a specific table
    :param schema: Name of a schema
    :param table: Name of a table
    :return:
    """
    engine = actions._get_engine()
    # metadata = sqla.MetaData(bind=engine)
    Session = sessionmaker()
    session = Session(bind=engine)
    try:
        if table is None:
            # Neither table, not schema are defined
            result = session.execute(sqla.select([Tag]).order_by("name"))
            session.commit()
            r = [
                {
                    "id": r.id,
                    "name": r.name,
                    "name_normalized": r.name_normalized,
                    "color": "#" + format(r.color, "06X"),
                    "usage_count": r.usage_count,
                    "usage_tracked_since": r.usage_tracked_since,
                }
                for r in result
            ]
            return sort_tags_by_popularity(r)

        if schema is None:
            # default schema is the public schema
            schema = "public"

        result = session.execute(
            session.query(
                Tag.name.label("name"),
                Tag.name_normalized.label("name_normalized"),
                Tag.id.label("id"),
                Tag.color.label("color"),
                Tag.usage_count.label("usage_count"),
                Tag.usage_tracked_since.label("usage_tracked_since"),
                TableTags.table_name,
            )
            .filter(TableTags.tag == Tag.id)
            .filter(TableTags.table_name == table)
            .filter(TableTags.schema_name == schema)
            .order_by("name")
        )
        session.commit()
    finally:
        session.close()
    r = [
        {
            "id": r.id,
            "name": r.name,
            "name_normalized": r.name_normalized,
            "color": "#" + format(r.color, "06X"),
            "usage_count": r.usage_count,
            "usage_tracked_since": r.usage_tracked_since,
        }
        for r in result
    ]
    return sort_tags_by_popularity(r)


def sort_tags_by_popularity(tags):
    def key_func(tag):
        # track_time = tag["usage_tracked_since"] - datetime.datetime.utcnow()
        return tag["usage_count"]

    tags.sort(reverse=True, key=key_func)
    return tags


def get_popular_tags(schema=None, table=None, limit=10):
    tags = get_all_tags(schema, table)
    sort_tags_by_popularity(tags)

    return tags[:limit]


def increment_usage_count(tag_id):
    """
    Increment usage count of a specific tag
    :param tag_id: ID of the tag which usage count should be incremented
    :return:
    """
    engine = actions._get_engine()
    Session = sessionmaker()
    session = Session(bind=engine)

    try:
        result = session.query(Tag).filter_by(id=tag_id).first()
        if result:
            result.usage_count += 1

        session.commit()
    finally:
        session.close()


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
            }
        )
    return columns


class WizardView(LoginRequiredMixin, View):
    """View for the upload wizard (create tables, upload csv)."""

    def get(self, request, schema="model_draft", table=None):
        """Handle GET request (render the page)."""
        engine = actions._get_engine()

        can_add = False
        columns = None
        # pk_fields = None
        n_rows = None
        if table:
            # get information about the table
            # if upload: table must exist in schema model_draft
            if schema != "model_draft":
                raise Http404("Can only upload to schema model_draft")
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
                        "api_table_meta", kwargs={"schema": schema, "table": table}
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
        json_schema = OEMETADATA_V160_SCHEMA
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
        Sorts the metadata of a table into categories and adds the value
        suggestion and comment that were added during the review, to facilitate
        Further processing easier.

        Note:
            The categories spatial & temporal are often combined during visualization.

        Args:
            schema (str): The schema of the table.
            table (str): The name of the table.

        Returns:


        Examples:
            A return value can look like the below dictionary:

            >>>
            {
                "general": [
                    {
                    "field": "id",
                    "value": "http: //127.0.0.1:8000/dataedit/view/model_draft/test2",
                    "newValue": "",
                    "reviewer_suggestion": "",
                    "suggestion_comment": ""
                    }
                ],
                "spatial": [...],
                "temporal": [...],
                "source": [...],
                "license": [...],
            }

        """

        val = self.parse_keys(oemetadata)
        gen_key_list = []
        spatial_key_list = []
        temporal_key_list = []
        source_key_list = []
        license_key_list = []

        for i in val:
            fieldKey = list(i.values())[0]
            if fieldKey.split(".")[0] == "spatial":
                spatial_key_list.append(i)
            elif fieldKey.split(".")[0] == "temporal":
                temporal_key_list.append(i)
            elif fieldKey.split(".")[0] == "sources":
                source_key_list.append(i)
            elif fieldKey.split(".")[0] == "licenses":
                license_key_list.append(i)

            elif (
                fieldKey.split(".")[0] == "name"
                or fieldKey.split(".")[0] == "title"
                or fieldKey.split(".")[0] == "id"
                or fieldKey.split(".")[0] == "description"
                or fieldKey.split(".")[0] == "language"
                or fieldKey.split(".")[0] == "subject"
                or fieldKey.split(".")[0] == "keywords"
                or fieldKey.split(".")[0] == "publicationDate"
                or fieldKey.split(".")[0] == "context"
            ):
                gen_key_list.append(i)

        meta = {
            "general": gen_key_list,
            "spatial": spatial_key_list,
            "temporal": temporal_key_list,
            "source": source_key_list,
            "license": license_key_list,
        }

        return meta

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
                    for attr in ["description", "example", "badge", "title"]
                ):
                    field_descriptions[key] = {}
                    if "description" in value:
                        field_descriptions[key]["description"] = value["description"]
                    if "example" in value:
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
        }
        return render(request, "dataedit/opr_review.html", context=context_meta)

    def post(self, request, schema, table, review_id=None):
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
            contributor = PeerReviewManager.load_contributor(schema, table)

            if contributor is not None:
                # Überprüfen, ob ein aktiver PeerReview existiert
                active_peer_review = PeerReview.load(schema=schema, table=table)
                if active_peer_review is None or active_peer_review.is_finished:
                    # Kein aktiver PeerReview vorhanden
                    # oder der aktive PeerReview ist abgeschlossen
                    table_review = PeerReview(
                        schema=schema,
                        table=table,
                        is_finished=review_finished,
                        review=review_datamodel,
                        reviewer=request.user,
                        contributor=contributor,
                        oemetadata=load_metadata_from_db(schema=schema, table=table),
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
                    f"as table holder for the current table: {table}!"
                )
                return JsonResponse({"error": error_msg}, status=400)

            # TODO: Check for schema/topic as reviewed finished also indicates the table
            # needs to be or has to be moved.
            if review_finished is True:
                review_table = Table.load(schema=schema, table=table)
                review_table.set_is_reviewed()
                metadata = self.load_json(schema, table, review_id=review_id)
                updated_metadata = recursive_update(metadata, review_data)
                save_metadata_to_db(schema, table, updated_metadata)
                active_peer_review = PeerReview.load(schema=schema, table=table)

                if active_peer_review:
                    updated_oemetadata = recursive_update(active_peer_review.oemetadata, review_data)
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

        Missing parts:
            - merge contributor field review and reviewer field review

        Args:
            request (HttpRequest): The incoming HTTP POST request.
            schema (str): The schema of the table.
            table (str): The name of the table.
            review_id (int): The ID of the review.

        Returns:
            HttpResponse: Rendered HTML response for contributor review.

        Note:
            This method has some missing parts regarding the merging of contributor
            and reviewer field review.
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
