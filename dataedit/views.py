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
from dataedit import models
from .models import TableRevision
from django.db.models import Q
from functools import reduce
import operator

session = None

""" This is the initial view that initialises the database connection """
excluded_schemas = [
    "information_schema",
    "public",
    "topology",
    "pg_catalog"
]


def listschemas(request):
    insp = actions.connect()
    schemas = sorted([(models.Schema.objects.get_or_create(name=schema)[0], len(
        {table for table in insp.get_table_names(schema=schema) if
         not table.startswith('_')})) for schema in insp.get_schema_names() if
                      schema not in excluded_schemas and not schema.startswith('_')], key=lambda x: x[0].name)
    return render(request, 'dataedit/dataedit_schemalist.html',
                  {'schemas': schemas})


def listtables(request, schema_name):

    if not actions.has_schema({'schema': '_'+schema_name}):
        actions.create_meta_schema(schema_name)

    insp = actions.connect()
    if schema_name in excluded_schemas:
        raise Http404("Schema not accessible")
    schema,_ = models.Schema.objects.get_or_create(name=schema_name)
    tables = []
    for table in insp.get_table_names(schema=schema_name):
        if not table.startswith('_'):
            t,_ = models.Table.objects.get_or_create(name=table, schema=schema)
            tables.append(t)
    tables = sorted(tables, key=lambda x: x.name)
    print([t.name for t in tables])
    return render(request, 'dataedit/dataedit_tablelist.html',
                  {'schema': schema, 'tables': tables})


COMMENT_KEYS = [('Name', 'Name'),
                ('Date of collection', 'Date_of_collection'),
                ('Spatial resolution', 'Spatial_resolution'),
                ('Description', 'Description'),
                ('Licence', 'Licence'),
                ('Column', 'Column'),
                ('Instructions for proper use', 'Proper_use'),
                ('Source', 'Source'),
                ('Reference date', 'Reference_date'),
                ('Original file', 'Original_file'),
                ('Spatial resolution', 'Spatial_resolution'),
                ('', ''), ]


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
    print(table)
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
    print(" ".join(L))
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
    print(response)
    return response


def show_revision(request, schema, table, rev_id):
    global pending_dumps
    fname = "{schema}/{table}.tar.gz".format(schema=schema,
                                             table=table)  # "{schema}_{table}_{rev_id}.sql".format(schema=schema, table=table, rev_id=rev_id)
    try:
        rev = TableRevision.objects.get(schema=schema, table=table,
                                        revision=rev_id)
        rev.last_accessed = timezone.now()
        rev.save()
        return send_dump(rev_id, schema, table)
    except TableRevision.DoesNotExist:

        if (schema, table, rev_id) in pending_dumps:
            if not pending_dumps[(schema, table, rev_id)].is_alive():
                pending_dumps.pop((schema, table, rev_id))
                rev = TableRevision(revision=rev_id, schema=schema, table=table)
                rev.save()
                return send_dump(rev_id, schema, table)
        else:
            t = threading.Thread(target=create_dump,
                                 args=(schema, table, rev_id, fname))
            t.start()
            pending_dumps[(schema, table, rev_id)] = t
        return render(request, 'dataedit/dataedit_revision_pending.html', {})


class DataView(View):
    """ This method handles the GET requests for the main page of data edit.
        Initialises the session data (if necessary)
    """

    def get(self, request, schema, table):

        if schema in excluded_schemas:
            raise Http404("Schema not accessible")
        db = sec.dbname
        tags = []

        if not actions.has_table(
                {'schema': actions.get_meta_schema_name(schema),
                 'table': actions.get_comment_table_name(table)}):
            actions.create_comment_table(schema, table)

        if not actions.has_table(
                {'schema': actions.get_meta_schema_name(schema),
                 'table': actions.get_edit_table_name(table)}):
            actions.create_edit_table(schema, table)

        if models.Table.objects.filter(name=table,
                                       schema__name=schema).exists():
            print(schema,table)
            tobj = models.Table.objects.get(name=table, schema__name=schema)
            tags = tobj.tags.all()

        comment_on_table = actions.get_comment_table(db, schema, table)
        comment_columns = {d["name"]: d for d in comment_on_table[
            "Table fields"]} if "Table fields" in comment_on_table else {}

        comment_on_table = OrderedDict(
            [(label, comment_on_table[key]) for key, label in
             COMMENT_KEYS
             if key in comment_on_table])

        columns = actions.get_columns({'schema': schema, 'table': table})
        has_row_comments = '_comment' in {col['name'] for col in columns if
                                          'name' in col}

        repo = svn.local.LocalClient(sec.datarepowc)
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


class TagUpdate(UpdateView):
    model = models.Tag
    fields = '__all__'
    template_name_suffix = '_form'

    @login_required(login_url='/login/')
    def dispatch(self, request, *args, **kwargs):
        return super(TagUpdate, self).dispatch(request, *args,
                                                          **kwargs)

@login_required(login_url='/login/')
def add_table_tags(request):
    schema = request.POST['schema']
    table = request.POST.get('table',None)
    obj, _ = models.Schema.objects.get_or_create(name=schema)
    if table:
        obj, _ = models.Table.objects.get_or_create(name=table, schema=obj)
    tab_tags = obj.tags.all()
    ids = {int(field[len('tag_'):]) for field in request.POST if field.startswith('tag_')}
    for tag in models.Tag.objects.filter(pk__in=ids):
        print(tag)
        if tag not in tab_tags:
            obj.tags.add(tag)
    for tag in tab_tags:
        if str(tag.pk) not in request.POST:
            obj.tags.remove(tag)
    obj.save()
    return redirect(request.META['HTTP_REFERER'])


class TagCreate(LoginRequiredMixin, CreateView):
    model = models.Tag
    fields = '__all__'
    success_url = '/dataedit'
    template_name_suffix = '_form'


class SearchView(View):
    def get(self, request):
        return render(request, 'dataedit/search.html', {'results': [], 'tags':models.Tag.objects.all()})

    def post(self, request):
        results = []
        print(request.POST)
        filter_tags = models.Tag.objects.filter(pk__in={key[len('select_'):] for key in request.POST if key.startswith('select_')})
        print(filter_tags)
        if 'string' in request.POST and request.POST['string']:
            search_string = '*+OR+*'.join(
                ('*' + request.POST['string'] + '*').split(' '))
            query = 'comment%3A{s}+OR+table%3A{s}+OR+schema%3A{s}'.format(
                s=search_string)
        else:
            query = '*:*'
        post = sec.SOLR_URL + 'select?q=' + query \
            + '&wt=json&rows=1000' \
            + '&fq=-(table:_*)'
        for schema in excluded_schemas:
            post += '&fq=-(schema:%s)'%schema
        response = requests.get(post)
        response = json.loads(response.text)
        print(len(response['response']['docs']))

        # The following is basicly a big "get_or_create" for possibly a lot of
        # schemas and tables that were returned by solr.
        # But it should be much faster this way.

        tables = {(result['schema'], result['table']) for result in
                  response['response']['docs']}
        query_set = reduce(operator.or_ ,{Q(schema__name=schema, name=table) for schema, table  in tables})
        results = models.Table.objects.filter(query_set)
        tables_found = {(res.schema.name, res.name) for res in results}
        schemas = {schema for schema,_ in tables}
        schema_mapper = {schema.name: schema for
                         schema in models.Schema.objects.filter(name__in=schemas)}
        new_schemas = []
        for schema_name in (schemas - schema_mapper.keys()):
            schema = models.Schema(name=schema_name)
            schema_mapper[schema_name] = schema
            new_schemas.append(schema)
        models.Schema.objects.bulk_create(new_schemas)

        new_tables = []
        for (schema,table) in tables - tables_found:
            table = models.Table(name=table,schema=schema_mapper[schema])
            new_tables.append(table)
        models.Table.objects.bulk_create(new_tables)

        if not filter_tags:
            results =  list(results)+new_tables

        results = [t for t in results if set(filter_tags.all()).issubset(t.tags.all())]
        return render(request, 'dataedit/search.html', {'results': results, 'tags':models.Tag.objects.all(), 'selected': filter_tags})

