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
    insp = actions.connect()
    schemas = sorted([(schema, len(
        {table for table in insp.get_table_names(schema=schema) if
         not table.startswith('_')})) for schema in insp.get_schema_names() if
                      schema in schema_whitelist and not schema.startswith('_')], key=lambda x: x[0])
    return render(request, 'dataedit/dataedit_schemalist.html',
                  {'schemas': schemas})


def read_label(table, comment):
    try:
        return json.loads(comment.replace('\n', ''))['Name'].strip() \
               + " (" + table + ")"
    except Exception as e:
        return None

def get_readable_table_names(schema):
    engine = actions._get_engine()
    conn = engine.connect()
    try:
        res = conn.execute('SELECT table_name as TABLE, obj_description(((\'{table_schema}.\' || table_name ))::regclass) as COMMENT ' \
                            'FROM information_schema.tables where table_schema=\'{table_schema}\';'.format(table_schema=schema))
    except Exception as e:
        raise e
        return {}
    finally:
        conn.close()
    return {table: read_label(table, comment) for (table,comment) in res}


def listtables(request, schema_name):
    insp = actions.connect()
    labels = get_readable_table_names(schema_name)
    tables = [(table, labels[table] if table in labels else None) for table in insp.get_table_names(schema=schema_name) if
              not table.startswith('_')]
    tables = sorted(tables, key=lambda x: x[0])
    return render(request, 'dataedit/dataedit_tablelist.html',
                  {'schema': schema_name, 'tables': tables})


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
    On success ta TableRevision will be stored to mark that the corresponding
    revision is available.

    :param request:
    :param schema:
    :param table:
    :param rev_id:
    :return:
    """

    fname = "{schema}/{table}.tar.gz".format(schema=schema,
                                             table=table)  # "{schema}_{table}_{rev_id}.sql".format(schema=schema, table=table, rev_id=rev_id)

    original = True # marks whether this method initialised the revision creation

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


class DataView(View):
    """ This method handles the GET requests for the main page of data edit.
        Initialises the session data (if necessary)
    """

    def get(self, request, schema, table):

        if schema not in schema_whitelist or schema.startswith('_'):
            raise Http404("Schema not accessible")

        tags = []
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

        repo = svn.local.LocalClient(sec.datarepowc)
        TableRevision.objects.all().delete()
        available_revisions = TableRevision.objects.filter(table=table,
                                                           schema=schema)
        revisions = []
        for rev in repo.log_default():
            try:
                rev_obj = available_revisions.get(revision=rev.revision)
            except TableRevision.DoesNotExist:
                rev_obj = None
            revisions.append((rev, rev_obj))
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
                          'tags': tags
                      })

    def post(self, request, schema, table):
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
    def get(self, request, schema, table):
        db = sec.dbname
        comment_on_table = actions.get_comment_table(db, schema, table)
        columns = actions.analyze_columns(db, schema, table)
        if 'error' in comment_on_table:
            comment_on_table = {'Notes':[comment_on_table['content']]}
        comment_on_table = {k.replace(' ', '_'): v for (k, v) in comment_on_table.items()}
        if 'Column' not in comment_on_table:
            comment_on_table['Column'] = []
        commented_cols = [col['Name'] for col in comment_on_table['Column']]
        for col in columns:
            if not col['id'] in commented_cols:
                comment_on_table['Column'].append({
                    'Name':col['id'],
                    'Description': '',
                    'Unit': ''})

        return render(request, 'dataedit/meta_edit.html',{
            'schema': schema,
            'table': table,
            'comment_on_table': comment_on_table
        })

    def post(self, request, schema, table):
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
            'Changes':[],
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
        assert(re.match(self.name_pattern,name))
        return name

    def _load_list(self, request, name):
        pattern = r'%s_(?P<index>\d*)'%name
        return [request.POST[key].replace("'","\'") for key in request.POST if re.match(pattern, key)]

    def _load_url_list(self, request, name):
        pattern = r'%s_name_(?P<index>\d*)' % name
        return [{
                    'Name':request.POST[key].replace("'","\'"),
                    'URL': request.POST[key.replace('_name_', '_url_')].replace("'","\'")
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
    ids = {int(field[len('tag_'):]) for field in request.POST if field.startswith('tag_')}
    schema = request.POST['schema']
    table = request.POST.get('table',None)
    engine = actions._get_engine()
    metadata = sqla.MetaData(bind=engine)
    Session = sessionmaker()
    session = Session(bind=engine)

    session.query(Table_tags).filter(Table_tags.table_name==table and Table_tags.schema_name==schema).delete()
    for id in ids:
        t = Table_tags(**{'schema_name':schema, 'table_name':table, 'tag':id})
        session.add(t)
    session.commit()
    return redirect(request.META['HTTP_REFERER'])


def get_all_tags(schema=None, table=None):
    engine = actions._get_engine()
    metadata = sqla.MetaData(bind=engine)
    Session = sessionmaker()
    session = Session(bind=engine)

    if table == None:
        # Neither table, not schema are defined
        result = session.execute(sqla.select([Tag]))
        session.commit()
        r = [{'id':r.id, 'name': r.name, 'color':"#" + format(r.color, '06X')} for r in result]
        return r

    if schema == None:
        # default schema is the public schema
        schema='public'

    result = session.execute(session.query(Tag.name.label('name'), Tag.id.label('id'), Tag.color.label('color'), Table_tags.table_name).filter(Table_tags.tag == Tag.id).filter(Table_tags.table_name == table).filter(Table_tags.schema_name == schema))
    session.commit()
    return [{'id':r.id, 'name': r.name, 'color':"#" + format(r.color, '06X')} for r in result]

class SearchView(View):
    def get(self, request):
        return render(request, 'dataedit/search.html', {'results': [], 'tags':get_all_tags()})

    def post(self, request):
        results = []
        engine = actions._get_engine()
        metadata = sqla.MetaData(bind=engine)
        Session = sessionmaker()
        session = Session(bind=engine)
        search_view = sqla.Table("meta_search", metadata, autoload=True)

        filter_tags = [int(key[len('select_'):]) for key in request.POST if key.startswith('select_')]

        tag_agg = array_agg(Table_tags.tag)
        query = session.query(search_view.c.schema.label('schema'), search_view.c.table.label('table'), tag_agg).outerjoin(Table_tags, (search_view.c.table == Table_tags.table_name) and (search_view.c.table == Table_tags.table_name))
        if filter_tags:
            query = query.having(tag_agg.contains(filter_tags))

        query = query.group_by(search_view.c.schema, search_view.c.table)
        results = session.execute(query)

        session.commit()
        ret = [{'schema': r.schema, 'table':r.table} for r in results]
        return render(request, 'dataedit/search.html', {'results': ret, 'tags':get_all_tags(), 'selected': filter_tags})

