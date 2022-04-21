import csv
import datetime
import json
import os
import re
import threading
import time
from functools import reduce
from io import TextIOWrapper
from itertools import chain
from operator import add
from subprocess import call
from wsgiref.util import FileWrapper

import numpy
import sqlalchemy as sqla
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.postgres.search import SearchQuery
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.db.models import Count, Aggregate
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.urls import reverse
from django.utils.encoding import smart_str
from django.views.generic import View
from django.views.generic.base import TemplateView
from sqlalchemy.dialects.postgresql import array_agg
from sqlalchemy.orm import sessionmaker

import api.parser
from api.actions import describe_columns
import oeplatform.securitysettings as sec
from api import actions as actions
from dataedit.metadata import load_metadata_from_db, read_metadata_from_post
from dataedit.metadata.widget import MetaDataWidget
from dataedit.models import Filter as DBFilter
from dataedit.models import Table
from dataedit.models import View as DBView
from dataedit.forms import GraphViewForm, LatLonViewForm, GeomViewForm
from dataedit.structures import TableTags, Tag
from login import models as login_models

from .models import (
    TableRevision,
    View as DataViewModel
)
from .metadata.__init__ import load_metadata_from_db
import requests as req


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

    cache = dict()
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

    searchedQueryString = request.GET.get("query")
    searchedTagIds = list(map(
        lambda t: int(t),
        request.GET.getlist("tags"),
    ))

    for tag_id in searchedTagIds:
        increment_usage_count(tag_id)

    filter_kwargs = dict(search=SearchQuery(" & ".join(p + ":*" for p in re.findall("[\w]+", searchedQueryString)),
                                            search_type="raw")) if searchedQueryString else {}
    response = Table.objects.filter(**filter_kwargs).values("schema__name").annotate(tables_count=Count("name"))

    engine = actions._get_engine()
    conn = engine.connect()
    Session = sessionmaker()
    session = Session(bind=conn)
    tags = {r[0]: set(r[1]) for r in session.query(TableTags.schema_name, array_agg(TableTags.tag)).group_by(TableTags.schema_name)}

    description = {
        "boundaries": "Data that depicts boundaries, such as geographic, administrative or political boundaries. Such data comes as polygons.",
        "climate": "Data related to climate and weather. This includes, for example, precipitation, temperature, cloud cover and atmospheric conditions.",
        "economy": "Data related to economic activities. Examples: sectoral value added, sectoral inputs and outputs, GDP, prices of commodities etc.",
        "demand": "Data on demand. Demand can relate to commodities but also to services.",
        "grid": "Energy transmission infrastructure. examples: power lines, substation, pipelines",
        "supply": "Data on supply. Supply can relate to commodities but also to services.",
        "environment": "environmental resources, protection and conservation. examples: environmental pollution, waste storage and treatment, environmental impact assessment, monitoring environmental risk, nature reserves, landscape",
        "society": "Demographic data such as population statistics and projections, fertility, mortality etc.",
        "model_draft": "Unfinished data of any kind. Note: there is no version control and data is still volatile.",
        "scenario": "Scenario data in the broadest sense. Includes input and output data from models that project scenarios into the future. Example inputs: assumptions made about future developments of key parameters such as energy prices and GDP. Example outputs: projected electricity transmission, projected greenhouse gas emissions. Note that inputs to one model could be an output of another model and the other way around.",
        "reference": "Contains sources, literature and auxiliary/helper tables that can help you with your work.",
        "emission": "Data on emissions. Examples: total greenhouse gas emissions, CO2-emissions, energy-related CO2-emissions, methane emissions, air pollutants etc.",
        "openstreetmap": "OpenStreetMap is a open project that collects and structures freely usable geodata and keeps them in a database for use by anyone. This data is available under a free license, the Open Database License.",
        "policy": "Data on policies and measures. This could, for example, include a list of renewable energy policies per European Member State. It could also be a list of climate related policies and measures in a specific country."
    }

    schemas = sorted(
        [
            (row["schema__name"], description.get(row["schema__name"], "No description"), row["tables_count"], tags.get(row["schema__name"], []))
            for row in response
            if row["schema__name"] in schema_whitelist
            and tags.get(row["schema__name"], set()).issuperset(searchedTagIds or set())
        ],
        key=lambda x: x[0],
    )

    return render(
        request,
        "dataedit/dataedit_schemalist.html",
        {
            "schemas": schemas,
            "query": searchedQueryString,
            "tags": searchedTagIds
        }
    )


def read_label(table, comment):
    """
    Extracts the readable name from @comment and appends the real name in parens.
    If comment is not a JSON-dictionary or does not contain a field 'Name' None
    is returned.

    :param table: Name to append

    :param comment: String containing a JSON-dictionary according to @Metadata

    :return: Readable name appended by the true table name as string or None
    """
    try:
        if comment.get("Name"):
            return (
                comment["Name"].strip() + " (" + table + ")"
            )
        elif comment.get("Title"):
            return (
                    comment["Title"].strip() + " (" + table + ")"
            )
        elif comment.get("title"):
            return (
                    comment["title"].strip() + " (" + table + ")"
            )
        elif comment.get("name"):
            return (
                    comment["name"].strip() + " (" + table + ")"
            )
        else:
            return None

    except Exception as e:
        return None


def get_readable_table_names(schema):
    """
    Loads all tables from a schema with their corresponding comments, extracts
    their readable names, if possible.

    :param schema: The schema name as string

    :return: A dictionary with that maps table names to readable names as returned by :py:meth:`dataedit.views.read_label`
    """
    engine = actions._get_engine()
    conn = engine.connect()
    try:
        res = conn.execute(
            "SELECT table_name as TABLE "
            "FROM information_schema.tables where table_schema='{table_schema}';".format(
                table_schema=schema
            )
        )
    except Exception as e:
        raise e
        return {}
    finally:
        conn.close()
    return {r[0]: read_label(r[0], load_metadata_from_db(schema, r[0])) for r in res}

def listtables(request, schema_name):
    """
    :param request: A HTTP-request object sent by the Django framework
    :param schema_name: Name of a schema
    :return: Renders the list of all tables in the specified schema
    """

    searchedQueryString = request.GET.get("query")
    searchedTagIds = list(map(int,
        request.GET.getlist("tags"),
    ))

    for tag_id in searchedTagIds:
        increment_usage_count(tag_id)

    labels = get_readable_table_names(schema_name)
    filter_kwargs = dict(search=SearchQuery(" & ".join(p+":*" for p in re.findall("[\w]+", searchedQueryString)), search_type="raw")) if searchedQueryString else {}

    engine = actions._get_engine()
    conn = engine.connect()
    Session = sessionmaker()
    session = Session(bind=conn)
    tag_query = session.query(TableTags.table_name, array_agg(TableTags.tag), array_agg(Tag.name), array_agg(Tag.color), array_agg(Tag.usage_count)).filter(
        TableTags.schema_name==schema_name, TableTags.tag==Tag.id).group_by(TableTags.table_name)

    tags = {r[0]: sorted([dict(id=ident, name=label, color="#" + format(color, "06X"), popularity=pop)
                   for ident, label, color, pop in zip(r[1], r[2], r[3], r[4])], key=lambda x: x["popularity"])
            for r in tag_query}

    tables = [
        (
            table.name,
            labels.get(table.name),
            tags.get(table.name, [])
        )
        for table in Table.objects.filter(schema__name=schema_name, **filter_kwargs)
    ]

    # Apply tag filter later on, because I am not smart enough to do it inline.
    tables = [tableEntry for tableEntry in tables
              if {tag["id"] for tag in tableEntry[2]}.issuperset(searchedTagIds or set())]

    tables = sorted(tables, key=lambda x: x[0])
    return render(
        request,
        "dataedit/dataedit_tablelist.html",
        {
            "schema": schema_name, "tables": tables,
            "query": searchedQueryString, "tags": searchedTagIds
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

    :param json_obj: An JSON-object - possibly a dictionary, a list or an elementary JSON-object (e.g a string)

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
    metadata = sqla.MetaData(bind=engine)
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
        "errorMsg": "Tag name is not valid" if request.GET.get("status") == "invalid" else ""
    }
        
    return render(request=request, template_name="dataedit/tag_overview.html", context=context)



@login_required
def tag_editor(request, id=""):
    tags = get_all_tags()

    create_new = True

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

    status = "" # error status if operation fails

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


def view_edit(request, schema, table):
    post_id = request.GET.get("id")
    if post_id:
        view = DBView.objects.get(id=post_id)
        context = {
            "type": view.type,
            "view": view,
            "schema": schema,
            "table": table,
            "filter": view.filter.all(),
        }
        if view.options is not None:
            context.update(view.options)
        return render(
            request, template_name="dataedit/view_editor.html", context=context
        )
    else:
        type = request.GET.get("type")
        return render(
            request,
            template_name="dataedit/view_editor.html",
            context={"type": type, "new": True, "schema": schema, "table": table},
        )


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
        columns = [
            (c, c)
            for c in describe_columns(schema, table).keys()
        ]
        formset = GraphViewForm(columns=columns)

        return render(request, 'dataedit/tablegraph_form.html', {'formset': formset})

    def post(self, request, schema, table):
        # save an instance of View, look at GraphViewForm fields in forms.py for information to the
        # options
        opt = dict(x=request.POST.get('column_x'), y=request.POST.get('column_y'))
        gview = DataViewModel.objects.create(
            name=request.POST.get('name'),
            table=table,
            schema=schema,
            type='graph',
            options=opt,
            is_default=request.POST.get('is_default', False)
        )
        gview.save()

        return redirect(
            "/dataedit/view/{schema}/{table}?view={view_id}".format(schema=schema, table=table, view_id=gview.id)
        )


class MapView(View):
    def get(self, request, schema, table, maptype):
        columns = [
            (c, c)
            for c in describe_columns(schema, table).keys()
        ]
        if maptype=="latlon":
            form = LatLonViewForm(columns=columns)
        elif maptype=="geom":
            form = GeomViewForm(columns=columns)
        else:
            raise Http404

        return render(request, 'dataedit/tablemap_form.html',
                      {'form': form})

    def post(self, request, schema, table, maptype):
        columns = [
            (c, c)
            for c in describe_columns(schema, table).keys()
        ]
        if maptype == "latlon":
            form = LatLonViewForm(request.POST, columns=columns)
            options = dict(
                lat=request.POST.get('lat'),
                lon=request.POST.get('lon')
            )
        elif maptype == "geom":
            form = GeomViewForm(request.POST, columns=columns)
            options = dict(
                geom=request.POST.get('geom')
            )
        else:
            raise Http404

        form.schema = schema
        form.table = table
        form.options = options
        if form.is_valid():
            view_id = form.save(commit=True)
            return redirect(
                "/dataedit/view/{schema}/{table}?view={view_id}".format(schema=schema, table=table, view_id=view_id)
            )
        else:
            return self.get(request, schema, table)


class DataView(View):
    """ This class handles the GET and POST requests for the main page of data edit.

        This view is displayed when a table is clicked on after choosing a schema on the website

        Initialises the session data (if necessary)
    """

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
        if schema not in schema_whitelist or schema.startswith("_"):
            raise Http404("Schema not accessible")

        tags = []  # TODO: Unused - Remove
        db = sec.dbname

        engine = actions._get_engine()

        if not engine.dialect.has_table(engine, table, schema=schema):
            raise Http404

        # create a table for the metadata linked to the given table
        actions.create_meta(schema, table)

        # the metadata are stored in the table's comment
        metadata = load_metadata_from_db(schema, table)

        meta_widget = MetaDataWidget(metadata)

        revisions = []

        # load the admin interface
        api_changes = change_requests(schema, table)
        data = api_changes.get("data")
        display_message = api_changes.get("display_message")
        display_items = api_changes.get("display_items")

        is_admin = False
        can_add = False # can upload data
        table_obj = Table.load(schema, table)
        if request.user and not request.user.is_anonymous:
            is_admin = request.user.has_admin_permissions(schema, table)
            level = request.user.get_table_permission_level(table_obj)
            can_add = level >= login_models.WRITE_PERM

        table_views = DBView.objects.filter(table=table).filter(schema=schema)

        default = DBView(name="default", type="table", table=table, schema=schema)

        view_id = request.GET.get("view")

        if view_id == "default":
            current_view = default
        else:
            try:
                # at first, try to use the view, that is passed as get argument
                current_view = table_views.get(id=view_id)
            except ObjectDoesNotExist:
                current_view = default

        table_views = list(chain((default,), table_views))



        context_dict = {
            "comment_on_table": dict(metadata),
            "meta_widget": meta_widget.render(),
            "revisions": revisions,
            "kinds": ["table", "map", "graph"],
            "table": table,
            "schema": schema,
            "tags": tags,
            "data": data,
            "display_message": display_message,
            "display_items": display_items,
            "views": table_views,
            "filter": current_view.filter.all(),
            "current_view": current_view,
            "is_admin": is_admin,
            "can_add": can_add,
            "host": request.get_host(),
        }

        context_dict.update(current_view.options)

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
    """ This method handles the GET requests for the main page of data edit.
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
        user = login_models.myuser.objects.filter(name=request.POST["name"]).first()
        table_obj = Table.load(schema, table)
        p, _ = login_models.UserPermission.objects.get_or_create(
            holder=user, table=table_obj
        )
        p.save()
        return self.get(request, schema, table)

    def __change_user(self, request, schema, table):
        user = login_models.myuser.objects.filter(id=request.POST["user_id"]).first()
        table_obj = Table.load(schema, table)
        p = get_object_or_404(login_models.UserPermission, holder=user, table=table_obj)
        p.level = request.POST["level"]
        p.save()
        return self.get(request, schema, table)

    def __remove_user(self, request, schema, table):
        user = get_object_or_404(login_models.myuser, id=request.POST["user_id"])
        table_obj = Table.load(schema, table)
        p = get_object_or_404(login_models.UserPermission, holder=user, table=table_obj)
        p.delete()
        return self.get(request, schema, table)

    def __add_group(self, request, schema, table):
        group = get_object_or_404(login_models.UserGroup, name=request.POST["name"])
        table_obj = Table.load(schema, table)
        p, _ = login_models.GroupPermission.objects.get_or_create(
            holder=group, table=table_obj
        )
        p.save()
        return self.get(request, schema, table)

    def __change_group(self, request, schema, table):
        group = get_object_or_404(login_models.UserGroup, id=request.POST["group_id"])
        table_obj = Table.load(schema, table)
        p = get_object_or_404(
            login_models.GroupPermission, holder=group, table=table_obj
        )
        p.level = request.POST["level"]
        p.save()
        return self.get(request, schema, table)

    def __remove_group(self, request, schema, table):
        group = get_object_or_404(login_models.UserGroup, id=request.POST["group_id"])
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

    t = session.query(TableTags.tag).filter_by(tag = tag_id, table_name = table, schema_name = schema)
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

    t = session.query(Tag).filter(Tag.id==tag_id)
    session.commit()
    return session.query(t.exists()).scalar() 


def get_tag_id_by_tag_name_normalized(session, tag_name):
    """
    Query the Tag tabley in schmea public to get the Tag ID.
    Tags are queried by unique field tag_name_normalized.

    Args:
        session ([type]): [description]
        tag_name ([type]): [description]

    Returns:
        int: Tag ID
        None: If Tag ID does not exists.

    """

    tag = session.query(Tag).filter(Tag.name_normalized==tag_name).first()
    session.commit()
    if tag is not None:
        return tag.id
    else:
        return None


def get_tag_name_normalized_by_id(session, tag_id):
    """
    Query the Tag table in schmea public to get the tag_name_normalized.
    Tags are queried by tag id.

    Args:
        session (sqilachemy): sqlalachemy session
        tag_id (int): The Tag ID

    Returns:
        None: If tag id does not exists.
        Str: Tag name normalized
    """

    tag = session.query(Tag).filter(Tag.id==tag_id).first()
    session.commit()
    if tag is not None:
        return tag.name_normalized
    else:
        return None


def add_existing_keyword_tag_to_table_tags(session, schema, table, keyword_tag_id):
    """
    Add a tag from the oem-keywords to the table_tags for the current table. 

    Args:
        session (sqilachemy): sqlalachemy session
        schema (str): Name of the schema
        table (str): Name of the table
        keyword_tag_id (int): The tag id that machtes to keyword tag name (by tag_name_normalized)

    Returns:
        any: Exception
    """

    if check_is_tag(session, keyword_tag_id):
    
        t = TableTags(**{"schema_name": schema, "table_name": table, "tag": keyword_tag_id})

        try:
            session.add(t)
            session.commit()
        except Exception as e:
            session.rollback() #Rollback the changes on error
            return e
        finally:
            session.close() #Close the connection


def process_oem_keywords(session, schema, table, tag_ids, removed_table_tag_ids, default_color_new_tag="#2E3638"):
    """_summary_

    Args:
        session (_type_): _description_
        schema (_type_): _description_
        table (_type_): _description_
        tag_ids (_type_): _description_

    Returns:
        _type_: _description_
    """

    # Empty or bad tag names
    invalid_tags=["", " ", "_", "-", "*"]

    # Get metadata json. Add Tages to "keywords" field in oemetadata and update (comment on table)
    # Returns oem v1.4.0 if metadata is empty from ./metadata/__init__.py/__LATEST
    table_oemetadata = load_metadata_from_db(schema, table)

    # if table_oemetadata is {}:
    #     from metadata.v151.template import OEMETADATA_V151_TEMPLATE
    #     table_oemetadata = OEMETADATA_V151_TEMPLATE
        # md, error = actions.try_parse_metadata(table_oemetadata)
        # print(md, error)

    

    # Keep, this are the tags that where added by the user via OEP website
    updated_oep_tags = [] 
    # this are OEM keywords that are new to the OEP tags
    kw_only = []
    # Keywords that are present as OEP tag but have to be assinged as table tag
    kw_is_oep_tag_but_not_oep_table_tag = []
    # sync. table tags and keywords
    updated_keywords = []

    for id in tag_ids:
        kw = get_tag_name_normalized_by_id(session, id)
        if kw is not None:
           updated_oep_tags.append(kw)


    for k in table_oemetadata["keywords"]:
        normalized_kw = Tag.create_name_normalized(k)
        keyword_tag_id = get_tag_id_by_tag_name_normalized(session, normalized_kw)
        if keyword_tag_id is None and k not in kw_only and k not in invalid_tags:
            kw_only.append(k)
        elif keyword_tag_id is not None and check_is_table_tag(session, schema, table, keyword_tag_id) is False \
            and k not in kw_is_oep_tag_but_not_oep_table_tag:
            
            kw_is_oep_tag_but_not_oep_table_tag.append(k)


    updated_keywords = updated_oep_tags + kw_only
    for k in kw_is_oep_tag_but_not_oep_table_tag:
        normalized_kw = Tag.create_name_normalized(k)
        tag_id = get_tag_id_by_tag_name_normalized(session, normalized_kw)
        if k is not None and k not in updated_oep_tags and [True for kw in table_oemetadata["keywords"] if k in kw] \
            and tag_id not in removed_table_tag_ids:
            add_existing_keyword_tag_to_table_tags(session, schema, table, tag_id)
            updated_keywords.append(k)
        

    for k in kw_only:
        default_color = default_color_new_tag
        add_tag(k, default_color)
        tag_id = get_tag_id_by_tag_name_normalized(session, k)
        if tag_id is not None:
            add_existing_keyword_tag_to_table_tags(session, schema, table, tag_id)
    

    table_oemetadata["keywords"] = updated_keywords
    return table_oemetadata


# FIXME: should use api.views.require_write_permission, but circular imports!
@login_required
def add_table_tags(request):
    """
    Updates the tags on a table according to the tag values in request.
    The update will delete all tags that are not present in request and add all tags that are.

    :param request: A HTTP-request object sent by the Django framework. The *POST* field must contain the following values:
        * schema: The name of a schema
        * table: The name of a table
        * Any number of values that start with 'tag_' followed by the id of a tag.
    :return: Redirects to the previous page
    """
    ids = {
        int(field[len("tag_") :]) for field in request.POST if field.startswith("tag_")
    }
    schema = request.POST["schema"]
    table = request.POST.get("table", None)
    

    engine = actions._get_engine()
    metadata = sqla.MetaData(bind=engine)
    Session = sessionmaker()
    session = Session(bind=engine)

    # Identify the table tag ids that the user removed from the table.
    # Usefull to distinguish between keywords that are tags and have to be assinged as table tags
    # and keywords that exist as tags but where removed by the use, and therefore should not be reassinged to the table
    removed_table_tag_ids = [tt.tag for tt in session.query(TableTags).filter(TableTags.table_name == table and TableTags.schema_name == schema) if tt.tag not in ids]

    session.query(TableTags).filter(
        TableTags.table_name == table and TableTags.schema_name == schema
    ).delete()
    for id in ids:
        t = TableTags(**{"schema_name": schema, "table_name": table, "tag": id})
        session.add(t)
    session.commit()
    
    # Add keywords from oemetadata to table tags and table tags to keywords
    updated_oem_json = process_oem_keywords(session, schema, table, ids, removed_table_tag_ids)    
    
    # TODO: reuse session from above?
    with engine.begin() as con:
        actions.set_table_metadata(table=table, schema=schema, metadata=updated_oem_json, cursor=con)        

    
    return redirect(request.META["HTTP_REFERER"])


def get_all_tags(schema=None, table=None):
    """
    Load all tags of a specific table
    :param schema: Name of a schema
    :param table: Name of a table
    :return:
    """
    engine = actions._get_engine()
    metadata = sqla.MetaData(bind=engine)
    Session = sessionmaker()
    session = Session(bind=engine)
    try:
        if table == None:
            # Neither table, not schema are defined
            result = session.execute(sqla.select([Tag]).order_by("name"))
            session.commit()
            r = [
                {
                    "id": r.id,
                    "name": r.name,
                    "color": "#" + format(r.color, "06X"),
                    "usage_count": r.usage_count,
                    "usage_tracked_since": r.usage_tracked_since,
                }
                for r in result
            ]
            return sort_tags_by_popularity(r)

        if schema == None:
            # default schema is the public schema
            schema = "public"

        result = session.execute(
            session.query(
                Tag.name.label("name"),
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
            "color": "#" + format(r.color, "06X"),
            "usage_count": r.usage_count,
            "usage_tracked_since": r.usage_tracked_since,
        }
        for r in result
    ]
    return sort_tags_by_popularity(r)


def sort_tags_by_popularity(tags):
    def key_func(tag):
        track_time = tag["usage_tracked_since"] - datetime.datetime.utcnow()
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

        We want the data type definition to be a simple string, e.g. decimal(10, 6) or varchar(128),
        so we need to combine the various fields (type, numeric_precision, numeric_scale, ...)
        """
        # for reverse validation, see also api.parser.parse_type(dt_string)
        dt = column_def['data_type'].lower()
        precisions = None
        if dt.startswith('character'):
            if dt == 'character varying':
                dt = 'varchar'
            else:
                dt = 'char'
            precisions = [column_def['character_maximum_length']]
        elif dt.endswith(' without time zone'): # this is the default
            dt =  dt.replace(' without time zone', '')
        elif re.match('(numeric|decimal)', dt):
            precisions = [column_def['numeric_precision'], column_def['numeric_scale']]
        elif dt == 'interval':
            precisions = [column_def['interval_precision']]
        elif re.match('.*int', dt) and re.match('nextval', column_def.get('column_default') or ''):
            #dt = dt.replace('int', 'serial')
            pass
        elif dt.startswith('double'):
            dt = 'float'
        if precisions:  # remove None
            precisions = [x for x in precisions if x is not None]
        if precisions:
            dt += '(%s)' % ', '.join(str(x) for x in precisions)
        return dt

    def get_pk_fields(constraints):
        """Get the column names that make up the primary key from the constraints definitions.

        NOTE: Currently, the wizard to create tables only supports single fields primary keys (which is advisable anyways)
        """
        pk_fields = []
        for _name, constraint in constraints.items():
            if constraint.get("constraint_type") == "PRIMARY KEY":
                m = re.match(r"PRIMARY KEY[ ]*\(([^)]+)", constraint.get("definition") or "")
                if m:
                    # "f1, f2" -> ["f1", "f2"]
                    pk_fields = [x.strip() for x in m.groups()[0].split(',')]
        return pk_fields

    _columns = actions.describe_columns(schema, table)
    _constraints = actions.describe_constraints(schema, table)
    pk_fields = get_pk_fields(_constraints)
    # order by ordinal_position
    columns = []
    for name, col in sorted(_columns.items(), key=lambda kv: int(kv[1]['ordinal_position'])):
        columns.append({
            'name': name,
            'data_type': get_datatype_str(col),
            'is_nullable': col['is_nullable'],
            'is_pk': name in pk_fields
        })
    return columns


class WizardView(LoginRequiredMixin, View):
    """View for the upload wizard (create tables, upload csv).
    """

    def get(self, request, schema='model_draft', table=None):
        """Handle GET request (render the page).
        """
        engine = actions._get_engine()

        can_add = False
        columns = None
        pk_fields = None
        n_rows = None
        if table:
            # get information about the table
            # if upload: table must exist in schema model_draft
            if schema != 'model_draft':
                raise Http404('Can only upload to schema model_draft')
            if not engine.dialect.has_table(engine, table, schema=schema):
                raise Http404('Table does not exist')
            table_obj = Table.load(schema, table)
            if not request.user.is_anonymous:
                user_perms = login_models.UserPermission.objects.filter(table=table_obj)
                level = request.user.get_table_permission_level(table_obj)
                can_add = level >= login_models.WRITE_PERM
            columns = get_column_description(schema, table)
            # get number of rows
            sql = "SELECT COUNT(*) FROM {schema}.{table}".format(schema=schema, table=table)
            res = actions.perform_sql(sql)
            n_rows = res['result'].fetchone()[0]

        context = {
            "config": json.dumps({ # pass as json string
                "canAdd": can_add,
                "columns": columns,
                "schema": schema,
                "table": table,
                "nRows": n_rows
            }),
            "schema": schema,
            "table": table,
            "can_add": can_add
        }

        return render(request, "dataedit/wizard.html", context=context)


class MetaEditView(LoginRequiredMixin, View):
    """Metadata editor (cliet side json forms)."""

    def get(self, request, schema, table):
        columns = get_column_description(schema, table)

        can_add = False
        table_obj = Table.load(schema, table)
        if not request.user.is_anonymous:
            level = request.user.get_table_permission_level(table_obj)
            can_add = level >= login_models.WRITE_PERM

        url_table_id = request.build_absolute_uri(reverse('view', kwargs={"schema": schema, "table": table}))

        context_dict = {
            "config": json.dumps({
                "schema": schema,
                "table": table,
                "columns": columns,
                "url_table_id": url_table_id,
                "url_api_meta": reverse('api_table_meta', kwargs={"schema": schema, "table": table}),
                "url_view_table": reverse('view', kwargs={"schema": schema, "table": table}),
            }),
            "can_add": can_add
        }

        return render(
            request,
            "dataedit/meta_edit.html",
            context=context_dict,
        )
