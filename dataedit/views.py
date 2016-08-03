from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse,  HttpResponseForbidden, HttpResponseNotAllowed
import sqlalchemy as sqla
from .forms import InputForm, UploadFileForm, UploadMapForm
from django.views.generic import View
from django.template import RequestContext
import csv
import os
import oeplatform.securitysettings as sec
from django.views.decorators.csrf import csrf_exempt
import urllib.request as request
from django.core.exceptions import PermissionDenied
from api import actions
from collections import OrderedDict
import re
import svn.local
from .models import TableRevision
import json
import threading
from subprocess import call
from django.utils.encoding import smart_str
from wsgiref.util import FileWrapper
from django.utils import timezone
import math

session = None

""" This is the initial view that initialises the database connection """
excluded_schemas = [

    "information_schema",
    "public",
    "topology",
    "reference",
]
def listschemas(request):
    insp = connect()
    schemas = {schema for schema in  insp.get_schema_names() if schema not in excluded_schemas}
    return render(request, 'dataedit/dataedit_schemalist.html',{'schemas':schemas})

def listtables(request, schema):
    insp = connect()

    tables =  {table for table in insp.get_table_names(schema=schema) if not table.startswith('_')}
    return render(request, 'dataedit/dataedit_tablelist.html',{'schema':schema, 'tables':tables})


COMMENT_KEYS = [('Name', 'Name'),
                ('Date of collection', 'Date of collection'),
                ('Spatial resolution', 'Spatial resolution'),
                ('Description', 'Description'),
                ('Licence', 'Licence'),
                ('Instructions for proper use', 'Proper use'),
                ('Source', 'Source'),
                ('Reference date', 'Reference date'),
                ('Original file', 'Date of Collection'),
                ('Spatial resolution', ''),
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
    if not os.path.exists('dumps/{rev}'.format(rev=rev_id)):
        os.mkdir(sec.MEDIA_ROOT+'/dumps/{rev}'.format(rev=rev_id))
    if not os.path.exists(sec.MEDIA_ROOT+'/dumps/{rev}/{schema}'.format(rev=rev_id,schema=schema)):
        os.mkdir(sec.MEDIA_ROOT+'/dumps/{rev}/{schema}'.format(rev=rev_id,schema=schema))
    L =['svn', 'export', "file://"+sec.datarepo+name, '--force', '--revision='+rev_id, '-q',  sec.MEDIA_ROOT+'/dumps/'+rev_id+'/'+name]
    print(" ".join(L))
    return call(L, shell=False)
    """return call(["pg_dump",
                 "--port=%s"%sec.dbport,
                 "test",
                 "--schema=%s"%schema,
                 "--table=%s.%s"%(schema,table),
                 "--username={user}".format(
        user=sec.dbuser,
        pw=sec.dbpasswd),
                 "--host=%s"%sec.dbhost,
                 "--file=media/dumps/%s"%name,
                 "-w"], shell=False)"""

def send_dump(rev_id, schema, table):
    path = sec.MEDIA_ROOT+'/dumps/{rev}/{schema}/{table}.tar.gz'.format(rev=rev_id,schema=schema,table=table)
    f = FileWrapper(open(path, "rb"))
    response = HttpResponse(f,content_type='application/x-gzip')  # mimetype is replaced by content_type for django 1.7

    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str('{table}.tar.gz'.format(table=table))

    # It's usually a good idea to set the 'Content-Length' header too.
    # You can also set any other required headers: Cache-Control, etc.
    print(response)
    return response

def show_revision(request, schema, table, rev_id):
    global pending_dumps
    fname = "{schema}/{table}.tar.gz".format(schema=schema, table=table)#"{schema}_{table}_{rev_id}.sql".format(schema=schema, table=table, rev_id=rev_id)
    try:
        rev = TableRevision.objects.get(schema=schema, table=table,
                                               revision=rev_id)
        rev.last_accessed = timezone.now()
        rev.save()
        return send_dump(rev_id, schema, table)
    except TableRevision.DoesNotExist:

        if (schema,table,rev_id) in pending_dumps:
            if not pending_dumps[(schema,table,rev_id)].is_alive():
                pending_dumps.pop((schema,table,rev_id))
                rev = TableRevision(revision=rev_id, schema=schema, table=table)
                rev.save()
                return send_dump(rev_id, schema, table)
        else:
            t = threading.Thread(target=create_dump, args=(schema,table,rev_id,fname))
            t.start()
            pending_dumps[(schema, table, rev_id)] = t
        return render(request, 'dataedit/dataedit_revision_pending.html', {})

class DataView(View):

    """ This method handles the GET requests for the main page of data edit.
        Initialises the session data (if necessary)
    """

    def get(self, request, schema, table):
        #if any((x not in request.session for x in ["table", "schema", "fields", "headers", "floatingRows"])) or (
        #        request.session['table'] != table or request.session['schema'] != schema):
        #    error = loadSessionData(request, connect(db), db, schema, table)
        #    if error:
        #        return error
        # db = url.split("/")[1]
        page = int(request.GET.get('page', 1))
        limit = request.GET.get('limit', 100)
        db = sec.dbname
        count = actions.count_all(db, schema, table)

        page_num = max(math.ceil(count/limit), 1)
        last_page = min(page_num, page + 3)

        pages = range(max(1,page-3), last_page)
        (result, references) = actions.search(db, schema, table, offset=min((page-1)*limit, (page_num-1)*limit), limit=limit)

        header = actions._get_header(result)
        comment = actions.get_comment_table(db, schema, table)
        comment_columns = {d["name"]: d for d in comment[
            "Table fields"]} if "Table fields" in comment else {}

        comment = OrderedDict(
            [(label, comment[key]) for key, label in
             COMMENT_KEYS
             if key in comment])
        _, comment = _type_json(comment)
        references = [(dict(ref)['entries_id'], ref) for ref in references]
        rows = []
        header = [h["id"] for h in header]
        for row in result:
            """if '_comment' in row and row['_comment']:
    row['_comment'] = {'method': com.method, 'assumption': list(
                    com.assumption) if com.assumption != "null" else {},
                                    'origin': com.origin} for com in
                                   actions.search(db, schema,
                                                  '_' + table + '_cor',
                                                  pk=('id', row['_comment']))[0]
                                   if com.id == row['_comment']][0]"""
            rows.append(list(zip(header,row)))
        # res = [[row[h["id"]] for h in header] for row in result]

        repo = svn.local.LocalClient(sec.datarepowc)
        available_revisions = TableRevision.objects.filter(table=table, schema=schema)
        revisions = []
        revision_ids = [rev.revision for rev in available_revisions]
        print(available_revisions)
        for rev in repo.log_default():
            try:
                rev_obj = available_revisions.get(revision=rev.revision)
            except TableRevision.DoesNotExist:
                rev_obj = None
            print(rev_obj)
            revisions.append((rev, rev_obj))

        return render(request, 'dataedit/dataedit_overview.html',{"dataset": rows,
                "header": header,
                #'resource_view_json': json.dumps(data_dict['resource_view']),
                'references': references,
                'comment_table': comment,
                'comment_columns': comment_columns,
                'revisions': revisions,
                'kind': 'table',
                'table': table,
                'pages': pages,
                'page': page,
                'page_num':page_num,
                'last_page':last_page})
        print(list(map(lambda x:zip(request.session['headers'],x),request.session['floatingRows'])))
        return render(request, 'dataedit/dataedit_overview.html',
                      {'data': map(lambda x:zip(request.session['headers'],x),request.session['floatingRows'])})


"""
This View handles new data input and edit
"""


class DataInputView(View):

    """
    Handles the GET-request for the data edit and entry page. Requests
    may contain an id, if pending data shall be edited.
    """

    def get(self, request):
        self.form = InputForm(fields=request.session['fields'])

        did = None
        if "id" in request.GET:
            did = int(request.GET["id"])
            for field, entry in zip(request.session['headers'], request.session[
                                    'floatingRows'][did]):
                self.form.fields[field].initial = entry

        return render(request, 'dataedit/dataedit.html',
                      {'form': self.form, 'internal_oe_id': did, 'pks':request.session['primaryKeys']})

    """ Handles the POST-request for the data edit and entry page. Requests
        may contain an id, if pending data shall be edited.
    """

    def post(self, request):
        request.session.set_test_cookie()
        print(request.POST)
        newRow = [request.POST[head] for head in request.session['headers']]
        pkvals = {pk:request.POST[pk] for pk in request.session["primaryKeys"]}
        
        if not validatePks(request.session["db"],
            request.session["schema"],
            request.session["table"],    
            pkvals):
            form = InputForm(fields=request.session['fields'],values=request.POST)
            return render(request, 'dataedit/dataedit.html',
                      {'form': form, 
                      'internal_oe_id':request.POST["internal_oe_id"],
                      'pks':request.session['primaryKeys'],
                      'errors':["Primary Key is already present"]})
            
            
        did = request.POST["internal_oe_id"]
        if did not in [None, 'None']:
            did = int(did)
            request.session['floatingRows'][did] = newRow
        else:
            request.session['floatingRows'].append(newRow)
        return _renderTable(request)

"""
This View yields an upload functionality for CSV-files
"""


class DataUploadView(View):

    def post(self, request):
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            return render(request, 'dataedit/dataedit_map.html',
                          {'form': form})
        else:
            return render(
                request, 'dataedit/dataedit_upload.html', {'form': form})

    def get(self, request):
        form = UploadFileForm()
        return render(request, 'dataedit/dataedit_upload.html', {'form': form})

"""
This View allows the user to specifies how each the table columns relate to the
csv columns
"""


class DataMapView(View):

    def post(self, request):
        def store(f):
            dname = 'tmp/' + f.name
            with open(dname, 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)
            return dname
        datafile = store(request.FILES['file'])
        with open(datafile, 'r') as outf:
            reader = csv.reader(outf, delimiter='\t', quotechar='"')
            headers = next(reader)
            request.session['data'] = (
                headers, [next(reader) for _ in range(10)])
            form = UploadMapForm(
                fields=request.session['fields'],
                headers=headers)
        os.remove(datafile)  # TODO: Unsicher!
        return render(request, 'dataedit/dataedit_map.html', {'form': form})


"""
Deletes the request.POST["id"]-th entry
"""


def delete(request):
    if request.POST["id"] is not None:
        did = int(request.POST["id"])
        request.session['floatingRows'] = request.session['floatingRows'][
            :did] + request.session['floatingRows'][did + 1:]
    return redirect('/dataedit/view/{db}/{schema}/{table}'.format(db=request.session['db'],
                schema=request.session['schema'],
                table=request.session['table']),
                    {'data': request.session['floatingRows'],
                        'headers': request.session['headers']})

def commit(request):
    engine = _get_engine(sec.db)
    
    # load schema name and check for sanity    
    schema = request.session.pop("schema", None)
    if not is_pg_qual(schema):
        raise p.toolkit.ValidationError("Invalid schema name")    
    # Check whether schema exists
    
    # load table name and check for sanity
    table = request.session.pop("table", None)
    if not is_pg_qual(table):
        raise p.toolkit.ValidationError("Invalid table name") 

    fields = request.session.pop("fields",[])
    fieldnames = [f[0] for f in fields]
    if not fields == ["*"] and not all(map(is_pg_qual,fieldnames)):
        raise p.toolkit.ValidationError("Invalid field name")    

    data = request.session.pop("floatingRows",[])
    meta = sqla.MetaData()
    tab = sqla.Table(table,meta,schema=schema,autoload=True,autoload_with=engine)
    connection = engine.connect()
    
    connection.execute(
        tab.insert(),
        *[dict(zip(fieldnames,row)) for row in data]
    )

"""
    Constructs the new rows for @table using the mapping specified in dataedit_map.html
"""

def confirm(request):
    (csv_headers, rows) = request.session["data"]
    for row in rows:
        newRow = []
        for head in request.session['headers']:
            if request.POST[head] == "---":
                newRow.append(None)
            else:
                newRow.append(row[csv_headers.index(request.POST[head])])
        request.session['floatingRows'].append(newRow)
    return _renderTable(request)


""" Connects to the specified table using the security infomation stored in
securitysettings.py"""




def loadSessionData(request, insp,  schema, table):
    print(schema,table)
    if not all(map(is_pg_qual,[db,schema,table])):
        return HttpResponseForbidden()
    request.session['table'] = table
    request.session['schema'] = schema
    
    fields = [(c["name"], str(c["type"]))
                                 for c in insp.get_columns(table, schema=schema)]
    if not all(map(is_pg_qual,[f[0] for f in fields])):
        return HttpResponseForbidden()
    request.session['fields'] = fields
    request.session['headers'] = [x[0] for x in request.session['fields']]
    request.session['primaryKeys'] = insp.get_primary_keys(table, schema=schema)
    request.session['floatingRows'] = []

@csrf_exempt
def dropSessionData(request):
    print(request.method)
    if not (request.is_ajax() or request.method=='POST'):
        return HttpResponseNotAllowed(['POST'])
    del request.session['floatingRows']
    request.session['floatingRows'] = []
    return HttpResponse('ok')

def _renderTable(request):
    L = request.session['floatingRows']
    del request.session['floatingRows']
    request.session['floatingRows'] = L
    return redirect('/dataedit/view/{db}/{schema}/{table}'.format(
                db=request.session['schema'],
                schema=request.session['schema'], 
                table=request.session['table']),
                    {})
                    
                    
# DB Utils

def validatePks(schema, table, pkValues):
    engine = _get_engine()
    connection = engine.connect()
    meta = sqla.MetaData()
    tab = sqla.Table(table,meta,schema=schema,autoload=True,autoload_with=engine)
    where = " and ".join(["{k}={v}".format(k=k,v=v) for (k,v) in pkValues.items()])
    print(pkValues)
    result = connection.execute(tab.select(whereclause=where))
    f = result.first()
    print(f)
    return f == None
    
def connect():
    engine = _get_engine()
    insp = sqla.inspect(engine)
    return insp

def _get_engine():
    engine = sqla.create_engine(
        'postgresql://{0}:{1}@{2}:{3}/{4}'.format(
            sec.dbuser,
            sec.dbpasswd,
            sec.dbhost,
            sec.dbport,
            sec.dbname))
    return engine
def is_pg_qual(x):
    pgsql_qualifier = re.compile(r"^[\w\d_]+$")
    return pgsql_qualifier.search(x)

