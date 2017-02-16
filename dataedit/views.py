import json
import os
import threading
from collections import OrderedDict
from subprocess import call
from wsgiref.util import FileWrapper

import requests
import svn.local
from django.http import HttpResponse, \
    Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.encoding import smart_str
from django.views.generic import View, CreateView, UpdateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

import oeplatform.securitysettings as sec

from api import actions
from .models import TableRevision
from django.db.models import Q
from functools import reduce
import operator
import time
from django_ajax.decorators import ajax
import csv
import codecs
from io import TextIOWrapper
import re
import sqlalchemy as sqla
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import array_agg, ARRAY
from dataedit.structures import Table_tags, Tag

session = None

""" This is the initial view that initialises the database connection """
schema_whitelist = [
    "demand",
    "economic",
    "emission",
    "environmental",
    "grid",
    "political_boundary",
    "social",
    "supply",
    "scenario",
    "weather",
    # "model_draft",
    "reference",
    "workshop"
]


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
    query = 'SELECT schemaname, count(tablename) as tables FROM pg_tables WHERE pg_has_role(\'{user}\', tableowner, \'MEMBER\') AND tablename NOT LIKE \'\_%%\' group by schemaname;'.format(
        user=sec.dbuser)
    response = conn.execute(query)
    schemas = sorted([(row.schemaname, row.tables) for row in response if
                      row.schemaname in schema_whitelist and not row.schemaname.startswith('_')], key=lambda x: x[0])
    print(schemas)
    return render(request, 'dataedit/dataedit_schemalist.html', {'schemas': schemas})


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
        return json.loads(comment.replace('\n', ''))['Name'].strip() \
               + " (" + table + ")"
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
            'SELECT table_name as TABLE, obj_description(((\'{table_schema}.\' || table_name ))::regclass) as COMMENT ' \
            'FROM information_schema.tables where table_schema=\'{table_schema}\';'.format(table_schema=schema))
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
    query = 'SELECT tablename FROM pg_tables WHERE schemaname = \'{schema}\' ' \
            'AND pg_has_role(\'{user}\', tableowner, \'MEMBER\');'.format(
        schema=schema_name, user=sec.dbuser)

    tables = conn.execute(query)
    tables = [(table.tablename, labels[table.tablename] if table.tablename in labels else None,
               get_indication_color(table.tablename, schema_name)[0]) for table in tables if
              not table.tablename.startswith('_')]
    tables = sorted(tables, key=lambda x: x[0])

    return render(request, 'dataedit/dataedit_tablelist.html',
                  {'schema': schema_name, 'tables': tables})


def get_indication_color(table, schema):
    """

    :rtype: tuple
    """
    red_color = "#FF0000"
    yellow_color = "#FFA500"
    green_color = "#008000"

    db = sec.dbname
    comment_on_table = actions.get_comment_table(db, schema, table)

    """
    red: Serve violations (forbidden symbols in name, not owned by the database user used by the platform, meta-data missing)
    yellow: Minor violations (meta-data incomplete)
    green: Everything seems fine
    """

    return_color = green_color
    return_reason = ""
    return_code = 0

    # Meta-Data

    # Check for meta-data incomplete

    incomplete_meta_data = [] in comment_on_table.values()
    if incomplete_meta_data:
        return_color = yellow_color
        return_reason = "Incomplete meta-data."
        return_code = 1

    # Check for meta-data missing

    no_metadata = True

    for key in comment_on_table:
        if comment_on_table[key] != "":
            no_metadata = False
        break

    if no_metadata:
        return_color = red_color
        return_reason = "Missing complete meta-data."
        return_code = 2

    # Not allowed symbols

    not_allowed_symbols = [',', '.', ' ']

    for symbol in not_allowed_symbols:
        if symbol in table:
            return_color = red_color
            return_reason = "Forbidden symbols in name."
            return_code = 2

    if not table.islower():
        return_color = red_color
        return_reason = "Bad formatting in name."
        return_code = 2


    return return_color, return_reason, return_code


COMMENT_KEYS = [('Name', 'Name'),
                ('Date of collection', 'Date_of_Collection'),
                ('Spatial resolution', 'Spatial_Resolution'),
                ('Description', 'Description'),
                ('Licence', 'Licence'),
                ('Column', 'Column'),
                ('Instructions for proper use', 'Instructions_for_proper_use'),
                ('Source', 'Source'),
                ('Reference date', 'Reference_date'),
                ('Original file', 'Original_file'),
                ('Notes', 'Notes'), ]


def _type_json(json_obj):
    """
    Recursively labels JSON-objects by their types. Singleton lists are handled
    as elementary objects.

    :param json_obj: An JSON-object - possibly a dictionary, a list or an elementary JSON-object (e.g a string)

    :return: An annotated JSON-object (type, object)

    """
    if isinstance(json_obj, dict):
        return 'dict', [(k, _type_json(json_obj[k]))
                        for k
                        in json_obj]
    elif isinstance(json_obj, list):
        if len(json_obj) == 1:
            return _type_json(json_obj[0])
        return 'list', [_type_json(e) for e in
                        json_obj]
    else:
        return str(type(json_obj)), json_obj


pending_dumps = {}


def create_dump(schema, table, rev_id, name):
    if not os.path.exists(sec.MEDIA_ROOT + '/dumps/{rev}'.format(rev=rev_id)):
        os.mkdir(sec.MEDIA_ROOT + '/dumps/{rev}'.format(rev=rev_id))
    if not os.path.exists(
                    sec.MEDIA_ROOT + '/dumps/{rev}/{schema}'.format(rev=rev_id,
                                                                    schema=schema)):
        os.mkdir(sec.MEDIA_ROOT + '/dumps/{rev}/{schema}'.format(rev=rev_id,
                                                                 schema=schema))
    L = ['svn', 'export', "file://" + sec.datarepo + name, '--force',
         '--revision=' + rev_id, '-q',
         sec.MEDIA_ROOT + '/dumps/' + rev_id + '/' + name]
    return call(L, shell=False)


def send_dump(rev_id, schema, table):
    path = sec.MEDIA_ROOT + '/dumps/{rev}/{schema}/{table}.tar.gz'.format(
        rev=rev_id, schema=schema, table=table)
    f = FileWrapper(open(path, "rb"))
    response = HttpResponse(f,
                            content_type='application/x-gzip')  # mimetype is replaced by content_type for django 1.7

    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(
        '{table}.tar.gz'.format(table=table))

    # It's usually a good idea to set the 'Content-Length' header too.
    # You can also set any other required headers: Cache-Control, etc.
    return response


def show_revision(request, schema, table, rev_id):
    global pending_dumps

    rev = TableRevision.objects.get(schema=schema, table=table,
                                    revision=rev_id)
    rev.last_accessed = timezone.now()
    rev.save()
    return send_dump(rev_id, schema, table)


@ajax
def request_revision(request, schema, table, rev_id):
    """
    This method handles an ajax request for a data revision of a specific table.
    On success the TableRevision-object will be stored to mark that the corresponding
    revision is available.

    :param request:
    :param schema:
    :param table:
    :param rev_id:
    :return:
    """

    fname = "{schema}/{table}.tar.gz".format(schema=schema,
                                             table=table)  # "{schema}_{table}_{rev_id}.sql".format(schema=schema, table=table, rev_id=rev_id)

    original = True  # marks whether this method initialised the revision creation

    # If some user already requested this dataset wait for this thread to finish
    if (schema, table, rev_id) in pending_dumps:
        t = pending_dumps[(schema, table, rev_id)]
        original = False
    else:
        t = threading.Thread(target=create_dump,
                             args=(schema, table, rev_id, fname))
        t.start()
        pending_dumps[(schema, table, rev_id)] = t

    while t.is_alive():
        time.sleep(10)

    pending_dumps.pop((schema, table, rev_id))
    if original:
        rev = TableRevision(revision=rev_id, schema=schema, table=table)
        rev.save()
    return {}


@login_required(login_url='/login/')
def tag_overview(request):
    return render(request=request, template_name='dataedit/tag_overview.html')


@login_required(login_url='/login/')
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

            assigned = session.query(Table_tags).filter(Table_tags.tag == t["id"]).count() > 0

            return render(request=request, template_name='dataedit/tag_editor.html',
                          context=
                          {
                              "name": tag['name'],
                              "id": tag['id'],
                              "color": tag['color'],
                              "assigned": assigned
                          })
    return render(request=request, template_name='dataedit/tag_editor.html',
                  context={"name": "", "color": "#000000", "assigned": False})


@login_required(login_url='/login/')
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

    return redirect('/dataedit/tags/')


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
    session.query(Table_tags).filter(Table_tags.tag == id).delete()

    # delete the tag from Tag
    session.query(Tag).filter(Tag.id == id).delete()

    session.commit()


def add_tag(name, color):
    engine = actions._get_engine()
    Session = sessionmaker()
    session = Session(bind=engine)

    session.add(Tag(**{'name': name, 'color': str(int(color[1:], 16)), 'id': None}))
    session.commit()


class DataView(View):
    """ This method handles the GET requests for the main page of data edit.
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
        if schema not in schema_whitelist or schema.startswith('_'):
            raise Http404("Schema not accessible")

        tags = []  # TODO: Unused - Remove
        db = sec.dbname
        actions.create_meta(schema, table)

        comment_on_table = actions.get_comment_table(db, schema, table)
        comment_columns = {d["name"]: d for d in comment_on_table[
            "Table fields"]} if "Table fields" in comment_on_table else {}

        if 'error' in comment_on_table:
            comment_on_table['Notes'] = [comment_on_table['content']]

        comment_on_table = OrderedDict(
            [(label, comment_on_table[key]) for key, label in
             COMMENT_KEYS
             if key in comment_on_table])

        columns = actions.get_columns({'schema': schema, 'table': table})
        has_row_comments = '_comment' in {col['name'] for col in columns if
                                          'name' in col}

        revisions = []
        try:
            repo = svn.local.LocalClient(sec.datarepowc)
            TableRevision.objects.all().delete()
            available_revisions = TableRevision.objects.filter(table=table,
                                                               schema=schema)

            for rev in repo.log_default():
                try:
                    rev_obj = available_revisions.get(revision=rev.revision)
                except TableRevision.DoesNotExist:
                    rev_obj = None
                revisions.append((rev, rev_obj))
        except:
            revisions = []

        indication_tuple = get_indication_color(table, schema)

        return render(request,
                      'dataedit/dataedit_overview.html',
                      {
                          'has_row_comments': has_row_comments,
                          'comment_on_table': dict(comment_on_table),
                          'comment_columns': comment_columns,
                          'revisions': revisions,
                          'kinds': ['table', 'map', 'graph'],
                          'table': table,
                          'schema': schema,
                          'tags': tags,
                          'indication_light': indication_tuple
                      })

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
            csvfile = TextIOWrapper(request.FILES['csv_file'].file,
                                    encoding=request.encoding)

            reader = csv.DictReader(csvfile, delimiter=',')

            actions.data_insert({
                'schema': schema,
                'table': table,
                'method': 'values',
                'values': reader
            }, {'user': request.user})
        return redirect('/dataedit/view/{schema}/{table}'.format(schema=schema,
                                                                 table=table))


class MetaView(View):
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
        db = sec.dbname
        comment_on_table = actions.get_comment_table(db, schema, table)
        columns = actions.analyze_columns(db, schema, table)
        if 'error' in comment_on_table:
            comment_on_table = {'Notes': [comment_on_table['content']]}
        comment_on_table = {k.replace(' ', '_'): v for (k, v) in comment_on_table.items()}
        if 'Column' not in comment_on_table:
            comment_on_table['Column'] = []
        commented_cols = [col['Name'] for col in comment_on_table['Column']]
        for col in columns:
            if not col['id'] in commented_cols:
                comment_on_table['Column'].append({
                    'Name': col['id'],
                    'Description': '',
                    'Unit': ''})

        return render(request, 'dataedit/meta_edit.html', {
            'schema': schema,
            'table': table,
            'comment_on_table': comment_on_table
        })

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
        columns = actions.analyze_columns(sec.dbname, schema, table)
        comment = {
            'Name': request.POST['name'],
            'Source': self._load_url_list(request, 'source'),
            'Reference date': self._load_list(request, 'ref_date'),
            'Date of Collection': self._load_list(request, 'date_col'),
            'Spatial Resolution': self._load_list(request, 'spat_res'),
            'Licence': self._load_url_list(request, 'licence'),
            'Description': self._load_list(request, 'descr'),
            'Column': self._load_col_list(request, columns),
            'Changes': [],
            'Notes': self._load_list(request, 'notes'),
            'Instructions for proper use': self._load_list(request, 'instr'),
        }
        engine = actions._get_engine()
        conn = engine.connect()
        trans = conn.begin()
        try:
            conn.execute(
                sqla.text("COMMENT ON TABLE {schema}.{table} IS :comment ;".format(
                    schema=schema,
                    table=table)),
                comment=json.dumps(comment)
            )
        except Exception as e:
            raise e
        else:
            trans.commit()
        finally:
            conn.close()
        return redirect('/dataedit/view/{schema}/{table}'.format(schema=schema,
                                                                 table=table))

    name_pattern = r'[\w\s]*'

    def loadName(self, name):
        """
        Checks whether the `name` contains only alphanumeric symbols and whitespaces
        :param name: A string
        :return: If the string is valid it is returned. Otherwise an AssertionError is raised.
        """
        assert (re.match(self.name_pattern, name))
        return name

    def _load_list(self, request, name):

        pattern = r'%s_(?P<index>\d*)' % name
        return [request.POST[key].replace("'", "\'") for key in request.POST if re.match(pattern, key)]

    def _load_url_list(self, request, name):
        pattern = r'%s_name_(?P<index>\d*)' % name
        return [{
                    'Name': request.POST[key].replace("'", "\'"),
                    'URL': request.POST[key.replace('_name_', '_url_')].replace("'", "\'")
                } for key in request.POST if
                re.match(pattern, key)]

    def _load_col_list(self, request, columns):
        return [{
                    'Name': col['id'],
                    'Description': request.POST['col_' + col['id'] + '_descr'],
                    'Unit': request.POST['col_' + col['id'] + '_unit']
                } for col in columns]


class CommentView(View):
    """ This method handles the GET requests for the main page of data edit.
        Initialises the session data (if necessary)
    """

    def get(self, request, schema, table):

        if schema not in schema_whitelist:
            raise Http404("Schema not accessible")

        tags = get_all_tags(schema=schema, table=table)

        return render(request,
                      'dataedit/comment_table.html',
                      {
                          'table': table,
                          'schema': schema,
                          'tags': tags
                      })

    def post(self, request, schema, table):
        if request.POST and request.FILES:
            csvfile = TextIOWrapper(request.FILES['csv_file'].file,
                                    encoding=request.encoding)

            reader = csv.DictReader(csvfile, delimiter=',')

            actions.data_insert({
                'schema': actions.get_meta_schema_name(schema),
                'table': actions.get_comment_table_name(table),
                'method': 'values',
                'values': reader
            }, {'user': request.user})
        return redirect('/dataedit/view/{schema}/{table}/comments'.format(schema=schema,
                                                                          table=table))


@login_required(login_url='/login/')
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
    ids = {int(field[len('tag_'):]) for field in request.POST if field.startswith('tag_')}
    schema = request.POST['schema']
    table = request.POST.get('table', None)
    engine = actions._get_engine()
    metadata = sqla.MetaData(bind=engine)
    Session = sessionmaker()
    session = Session(bind=engine)

    session.query(Table_tags).filter(Table_tags.table_name == table and Table_tags.schema_name == schema).delete()
    for id in ids:
        t = Table_tags(**{'schema_name': schema, 'table_name': table, 'tag': id})
        session.add(t)
    session.commit()
    return redirect(request.META['HTTP_REFERER'])


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

    if table == None:
        # Neither table, not schema are defined
        result = session.execute(sqla.select([Tag]))
        session.commit()
        r = [{'id': r.id, 'name': r.name, 'color': "#" + format(r.color, '06X')} for r in result]
        return r

    if schema == None:
        # default schema is the public schema
        schema = 'public'

    result = session.execute(session.query(Tag.name.label('name'), Tag.id.label('id'), Tag.color.label('color'),
                                           Table_tags.table_name).filter(Table_tags.tag == Tag.id).filter(
        Table_tags.table_name == table).filter(Table_tags.schema_name == schema))
    session.commit()
    return [{'id': r.id, 'name': r.name, 'color': "#" + format(r.color, '06X')} for r in result]


class SearchView(View):
    """

    """

    def get(self, request):
        """
        Renders an empty search field with a list of tags
        :param request: A HTTP-request object sent by the Django framework
        :return:
        """
        return render(request, 'dataedit/search.html', {'results': [], 'tags': get_all_tags()})

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

        filter_tags = [int(key[len('select_'):]) for key in request.POST if key.startswith('select_')]

        tag_agg = array_agg(Table_tags.tag)
        query = session.query(search_view.c.schema.label('schema'), search_view.c.table.label('table'),
                              tag_agg).outerjoin(Table_tags, (search_view.c.table == Table_tags.table_name) and (
            search_view.c.table == Table_tags.table_name))
        if filter_tags:
            query = query.having(tag_agg.contains(filter_tags))

        query = query.group_by(search_view.c.schema, search_view.c.table)
        results = session.execute(query)

        session.commit()
        ret = [{'schema': r.schema, 'table': r.table} for r in results]
        return render(request, 'dataedit/search.html',
                      {'results': ret, 'tags': get_all_tags(), 'selected': filter_tags})
