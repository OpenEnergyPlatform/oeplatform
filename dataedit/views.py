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

import oeplatform.securitysettings as sec
from api import actions
from dataedit import models
from .models import TableRevision

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
    schemas = sorted([(schema, len(
        {table for table in insp.get_table_names(schema=schema) if
         not table.startswith('_')})) for schema in insp.get_schema_names() if
                      schema not in excluded_schemas])
    return render(request, 'dataedit/dataedit_schemalist.html',
                  {'schemas': schemas})


def listtables(request, schema):
    insp = actions.connect()
    if schema in excluded_schemas:
        raise Http404("Schema not accessible")
    tables = sorted([table for table in insp.get_table_names(schema=schema) if
                     not table.startswith('_')])
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

        if models.Table.objects.filter(name=table,
                                       schema__name=schema).exists():
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
        print(actions.has_table(
            {'schema': schema, 'table': '_' + table + '_cor'}))
        has_row_comments = has_row_comments and actions.has_table(
            {'schema': schema, 'table': '_' + table + '_cor'})
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


def add_table_tag(request, schema, table, tag_id):
    sch, _ = models.Schema.objects.get_or_create(name=schema)
    tab, _ = models.Table.objects.get_or_create(name=table, schema=sch)
    tag = get_object_or_404(models.Tag, pk=tag_id)
    tab.tags.add(tag)
    tab.save()
    return redirect(request.GET.get('from', '/'))


class TagCreate(CreateView):
    model = models.Tag
    fields = '__all__'


class SearchView(View):
    def get(self, request):
        return render(request, 'dataedit/search.html', {'results': [], 'tags':models.Tag.objects.all()})

    def post(self, request):
        results = []
        print(request.POST)
        filter_tags = set([])
        if 'tags' in request.POST:
            filter_tags = request.POST.getlist('tags')
        if isinstance(filter_tags, str):
            filter_tags = {filter_tags}
        else:
            filter_tags = set(filter_tags)

        print(filter_tags)
        if request.POST['string']:
            search_string = '*+OR+*'.join(
                ('*' + request.POST['string'] + '*').split(' '))
            query = 'comment%3A{s}+OR+table%3A{s}+OR+schema%3A{s}'.format(
                s=search_string)
        else:
            query = '*:*'
        fq = '-table:_*'
        post = 'http://localhost:8983/solr/oedb_meta/select?q=' + query \
            + '&wt=json&rows=1000' \
            + '&fq=-(table:_*)'
        for schema in excluded_schemas:
            post += '&fq=-(schema:%s)'%schema
        response = requests.get(post)
        response = json.loads(response.text)
        print(response)
        for result in response['response']['docs']:
            table = result['table']
            schema = result['schema']
            tags = []
            if models.Table.objects.filter(name=table,
                                           schema__name=schema).exists():
                tobj = models.Table.objects.get(name=table,
                                                schema__name=schema)
                tags = tobj.tags.all()
            if filter_tags.issubset({tag.label for tag in tags}) and schema not in excluded_schemas:
                results.append((schema, table, tags))
            else:
                print((schema, table, tags))
        return render(request, 'dataedit/search.html', {'results': results, 'tags':models.Tag.objects.all()})
