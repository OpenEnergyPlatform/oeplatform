from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse,  HttpResponseForbidden
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

import re
session = None

""" This is the initial view that initialises the database connection """

def listdbs(request):
    return render(request, 'dataedit/dataedit_dblist.html',{})

def listschemas(request, db):
    print(db)
    insp = connect(db)
    schemas = {schema for schema in  insp.get_schema_names()}
    return render(request, 'dataedit/dataedit_schemalist.html',{'db':db, 'schemas':schemas})

def listtables(request, db, schema):
    print(db,schema)    
    insp = connect(db)
    
    tables =  {table for table in insp.get_table_names(schema=schema)}
    return render(request, 'dataedit/dataedit_tablelist.html',{'db':db, 'schema':schema, 'tables':tables})
    

class DataView(View):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)

    """ This method handles the GET requests for the main page of data edit.
        Initialises the session data (if necessary)
    """

    def get(self, request, db, schema, table):
        if any((x not in request.session for x in ["table", "schema", "fields", "headers", "floatingRows"])) or (
                request.session['table'] != table or request.session['schema'] != schema):
            error = loadSessionData(request, connect(db), db, schema, table)
            if error:
                return error
        return render(request, 'dataedit/dataedit_overview.html',
                      {'data': request.session['floatingRows'], 'headers': request.session['headers']})


"""
This View handles new data input and edit
"""


class DataInputView(View):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.id = None

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
        newRow = [request.POST[head] for head in request.session['headers']]
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)

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
    return redirect('view/{0}/{1}'.format(request.session['schema'],
                                          request.session['table']),
                    {'data': request.session['floatingRows'],
                        'headers': request.session['headers']})

def commit(request):
    db = request.session["db"]
    if db in ["test"]:
        engine = _get_engine(db)

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
    if not fields == ["*"] and not all(map(is_pg_qual,fields)):
        raise p.toolkit.ValidationError("Invalid field name")    

    data = data_dict.pop("data",[])
    meta = sqla.MetaData()
    tab = sqla.Table(table,meta,schema=schema,autoload=True,autoload_with=engine)
    connection = engine.connect()
    
    connection.execute(
        tab.insert(),
        *[dict(zip(fields,row)) for row in data]
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


def connect(db):
    if not all(map(is_pg_qual,[db])):
        raise PermissionDenied()
    engine = sqla.create_engine(
        'postgresql://{0}:{1}@{2}:{3}/{4}'.format(
            sec.dbuser,
            sec.dbpasswd,
            sec.dbhost,
            sec.dbport,
            db))
    insp = sqla.inspect(engine)
    return insp
    #users_table = meta.tables['app_renpassgis.scenario']

def is_pg_qual(x):
    pgsql_qualifier = re.compile(r"^[\w\d_]+$")
    return pgsql_qualifier.search(x)

def loadSessionData(request, insp, db, schema, table):
    print(db,schema,table)
    if not all(map(is_pg_qual,[db,schema,table])):
        return HttpResponseForbidden()
    request.session['db'] = db    
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
    print("DELETE")
    if not request.is_ajax() or not request.method=='POST':
        return HttpResponseNotAllowed(['POST'])
    request.session['floatingRows'] = []
    return HttpResponse('ok')

def _renderTable(request):
    L = request.session['floatingRows']
    del request.session['floatingRows']
    request.session['floatingRows'] = L
    return redirect('/dataedit/view/{0}/{1}'.format(request.session['schema'], request.session['table']),
                    {})

