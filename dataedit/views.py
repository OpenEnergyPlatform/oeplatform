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

import sqlalchemy as sqla
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.encoding import smart_str
from django.views.generic import View
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
from dataedit.forms import GraphViewForm
from dataedit.structures import TableTags, Tag
from login import models as login_models

from .models import (
    TableRevision,
    View as DataViewModel
)

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

    insp = actions.connect()
    engine = actions._get_engine()
    conn = engine.connect()
    query = (
        "SELECT schema_name, count(tablename) as tables "
        "FROM pg_tables right join information_schema.schemata "
        "ON schema_name=schemaname "
        "WHERE tablename IS NULL "
        "   OR (pg_has_role('{user}', tableowner, 'MEMBER') "
        "       AND tablename NOT LIKE '\_%%') "
        "GROUP BY schema_name;".format(user=sec.dbuser)
    )
    response = conn.execute(query)
    schemas = sorted(
        [
            (row.schema_name, row.tables)
            for row in response
            if row.schema_name in schema_whitelist
            and not row.schema_name.startswith("_")
        ],
        key=lambda x: x[0],
    )
    return render(request, "dataedit/dataedit_schemalist.html", {"schemas": schemas})


def overview(request):
    return render(request, "dataedit/dataedit_choices.html", {})


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
        return (
            json.loads(comment.replace("\n", ""))["Name"].strip() + " (" + table + ")"
        )
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
            "SELECT table_name as TABLE, obj_description((('\"{table_schema}\".\"' || table_name || '\"' ))::regclass) as COMMENT "
            "FROM information_schema.tables where table_schema='{table_schema}';".format(
                table_schema=schema
            )
        )
    except Exception as e:
        raise e
        return {}
    finally:
        conn.close()
    return {table: read_label(table, comment) for (table, comment) in res}


def listtables(request, schema_name):
    """
    :param request: A HTTP-request object sent by the Django framework
    :param schema_name: Name of a schema
    :return: Renders the list of all tables in the specified schema
    """
    engine = actions._get_engine()
    conn = engine.connect()
    labels = get_readable_table_names(schema_name)
    query = (
        "SELECT tablename FROM pg_tables WHERE schemaname = '{schema}' "
        "AND pg_has_role('{user}', tableowner, 'MEMBER');".format(
            schema=schema_name, user=sec.dbuser
        )
    )
    tables = conn.execute(query)
    tables = [
        (
            table.tablename,
            labels[table.tablename] if table.tablename in labels else None,
        )
        for table in tables
        if not table.tablename.startswith("_")
    ]
    tables = sorted(tables, key=lambda x: x[0])
    return render(
        request,
        "dataedit/dataedit_tablelist.html",
        {"schema": schema_name, "tables": tables},
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
        revisions = TableRevision.objects.filter(schema=schema, table=table)
        pending = [
            (schema, table, date)
            for (schema, table, date) in pending_dumps
            if schema == schema and table == table
        ]
        return render(
            request,
            "dataedit/dataedit_revision.html",
            {
                "schema": schema,
                "table": table,
                "revisions": revisions,
                "pending": pending,
            },
        )

    def post(self, request, schema, table, date=None):
        """
        This method handles an ajax request for a data revision of a specific table.
        On success the TableRevision-object will be stored to mark that the corresponding
        revision is available.

        :param request:
        :param schema:
        :param table:
        :param date:
        :return:
        """

        # date = time.strftime('%Y-%m-%d %H:%M:%S')
        # fname = time.strftime('%Y%m%d_%H%M%S', time.gmtime())

        date = time.strftime("%Y-%m-%d %H:%M:%S")
        # fname = time.strftime(schema+'_' + table + '%Y%m%d_%H%M%S', time.gmtime())

        fname = "20170814_000000"

        original = True  # marks whether this method initialised the revision creation

        # If some user already requested this dataset wait for this thread to finish
        if (schema, table, date) in pending_dumps:
            t = pending_dumps[(schema, table, date)]
            original = False
        else:
            t = threading.Thread(target=create_dump, args=(schema, table, fname))
            t.start()
            pending_dumps[(schema, table, date)] = t

        while t.is_alive():
            time.sleep(10)

        pending_dumps.pop((schema, table, date))
        if original:
            path = "/dumps/{schema}/{table}/{fname}.dump".format(
                fname=fname, schema=schema, table=table
            )
            size = os.path.getsize(sec.MEDIA_ROOT + path)
            rev = TableRevision(
                schema=schema, table=table, date=date, path="/media" + path, size=size
            )
            rev.save()
        return JsonResponse({})


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
    return render(request=request, template_name="dataedit/tag_overview.html")


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
    if "submit_save" in request.POST:
        if "tag_id" in request.POST:
            id = request.POST["tag_id"]
            name = request.POST["tag_text"]
            color = request.POST["tag_color"]
            edit_tag(id, name, color)
        else:
            name = request.POST["tag_text"]
            color = request.POST["tag_color"]
            add_tag(name, color)

    elif "submit_delete" in request.POST:
        id = request.POST["tag_id"]
        delete_tag(id)

    return redirect("/dataedit/tags/")


def edit_tag(id, name, color):
    engine = actions._get_engine()
    Session = sessionmaker()
    session = Session(bind=engine)

    result = session.query(Tag).filter(Tag.id == id).one()

    result.name = name
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


def create_graph(request, schema, table):

    if request.method == 'POST':
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
            "/dataedit/view/{schema}/{table}".format(schema=schema, table=table)
        )
    else:
        # get the columns id from the schema and the table
        columns = [
            (c, c)
            for c in describe_columns(schema, table).keys()
        ]
        formset = GraphViewForm(columns=columns)

        return render(request, 'dataedit/tablegraph_form.html', {'formset': formset})


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
        if request.user and not request.user.is_anonymous():
            is_admin = request.user.has_admin_permissions(schema, table)

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

        table_views = chain((default,), table_views)

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


class MetaView(LoginRequiredMixin, View):
    """

    """

    def get(self, request, schema, table):
        """
        Loads the metadata of the passed table and its columns.
        :param request: A HTTP-request object sent by the Django framework
        :param schema: Name of a schema
        :param table: Name of a table
        :return: Renders a form that contains a form with the tables metadata
        """

        metadata = load_metadata_from_db(schema, table)

        meta_widget = MetaDataWidget(metadata)

        context_dict = {
            "schema": schema,
            "table": table,
            "meta_widget": meta_widget.render_editmode(),
            "comment_on_table": metadata
        }

        return render(
            request,
            "dataedit/meta_edit.html",
            context=context_dict,
        )

    def post(self, request, schema, table):
        """
        Handles the send event of the form created in the get-method. The
        metadata is transformed into a JSON-dictionary and stored in the tables
        comment inside the database.
        :param request: A HTTP-request object sent by the Django framework
        :param schema: Name of a schema
        :param table: Name of a table
        :return: Redirects to the view of the specified table
        """
        columns = actions.analyze_columns(schema, table)

        comment = read_metadata_from_post(request.POST, schema, table)
        save_metadata_as_table_comment(schema, table, metadata=comment)

        return redirect(
            "/dataedit/view/{schema}/{table}".format(schema=schema, table=table)
        )


    name_pattern = r"[\w\s]*"

    def loadName(self, name):
        """
        Checks whether the `name` contains only alphanumeric symbols and whitespaces
        :param name: A string
        :return: If the string is valid it is returned. Otherwise an AssertionError is raised.
        """
        assert re.match(self.name_pattern, name)
        return name

    def _load_list(self, request, name):

        pattern = r"%s_(?P<index>\d*)" % name
        return [
            request.POST[key].replace("'", "'")
            for key in request.POST
            if re.match(pattern, key)
        ]

    def _load_url_list(self, request, name):
        pattern = r"%s_name_(?P<index>\d*)" % name
        return [
            {
                "Name": request.POST[key].replace("'", "'"),
                "URL": request.POST[key.replace("_name_", "_url_")].replace("'", "'"),
            }
            for key in request.POST
            if re.match(pattern, key)
        ]

    def _load_col_list(self, request, columns):
        return [
            {
                "Name": col["id"],
                "Description": request.POST["col_" + col["id"] + "_descr"],
                "Unit": request.POST["col_" + col["id"] + "_unit"],
            }
            for col in columns
        ]


def save_metadata_as_table_comment(schema, table, metadata):
    """Save metadata as comment string on a database table
    :param schema (string):
    :param table (string):
    :param metadata: structured data according to metadata specifications
    """
    # TODO: validate metadata!
    # metadata = validate(metadata)

    engine = actions._get_engine()
    conn = engine.connect()
    trans = conn.begin()
    try:
        conn.execute(
            sqla.text(
                "COMMENT ON TABLE {schema}.{table} IS :comment ;".format(
                    schema=schema, table=table
                )
            ),
            comment=json.dumps(metadata),
        )
    except Exception as e:
        raise e
    else:
        trans.commit()
    finally:
        conn.close()


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
        if not request.user.is_anonymous():
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
            request.user.is_anonymous()
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

    session.query(TableTags).filter(
        TableTags.table_name == table and TableTags.schema_name == schema
    ).delete()
    for id in ids:
        t = TableTags(**{"schema_name": schema, "table_name": table, "tag": id})
        session.add(t)
    session.commit()
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


class SearchView(View):
    """

    """

    def get(self, request):
        """
        Renders an empty search field with a list of tags
        :param request: A HTTP-request object sent by the Django framework
        :return:
        """
        return render(
            request, "dataedit/search.html", {"results": [], "tags": get_all_tags()}
        )

    def post(self, request):
        """

        :param request: A HTTP-request object sent by the Django framework. May contain a set of ids prefixed by *select_*
        :return:
        """
        results = []
        engine = actions._get_engine()
        metadata = sqla.MetaData(bind=engine)
        Session = sessionmaker()
        session = Session(bind=engine)
        search_view = sqla.Table("meta_search", metadata, autoload=True)

        filter_tags = [
            int(key[len("select_") :])
            for key in request.POST
            if key.startswith("select_")
        ]

        for tag_id in filter_tags:
            increment_usage_count(tag_id)

        tag_agg = array_agg(TableTags.tag)
        query = session.query(
            search_view.c.schema.label("schema"),
            search_view.c.table.label("table"),
            tag_agg,
        ).outerjoin(
            TableTags,
            (search_view.c.table == TableTags.table_name)
            and (search_view.c.table == TableTags.table_name),
        )
        if filter_tags:
            query = query.having(
                tag_agg.contains(sqla.cast(filter_tags, sqla.ARRAY(sqla.BigInteger)))
            )

        query = query.group_by(search_view.c.schema, search_view.c.table)
        results = session.execute(query)

        session.commit()
        ret = [{"schema": r.schema, "table": r.table} for r in results]
        return render(
            request,
            "dataedit/search.html",
            {"results": ret, "tags": get_all_tags(), "selected": filter_tags},
        )
