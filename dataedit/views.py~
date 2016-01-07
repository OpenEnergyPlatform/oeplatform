from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
import sqlalchemy as sqla
from .forms import InputForm, UploadFileForm, UploadMapForm
from django.views.generic import View
from django.template import RequestContext
import csv
import os
import oeplatform.securitysettings as sec
session = None


class DBView(View):
    def __init__(self, *args, **kwargs):
        print("New DBView")
        super(View,self).__init__(*args,*kwargs)
        engine = sqla.create_engine(
                    'postgresql://{0}:{1}@{2}:{3}/{4}'.format(
                    sec.dbuser,
                    sec.dbpasswd,
                    sec.dbhost,
                    sec.dbport,
                    sec.db))
        insp = sqla.inspect(engine)
        #users_table = meta.tables['app_renpassgis.scenario']
        self.fields = [(c["name"],str(c["type"])) 
            for c in insp.get_columns('scenario',schema='app_renpassgis')]

class DataInputView(DBView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args,*kwargs)       
        self.form = InputForm(fields=self.fields)
        self.id = None

    def get(self, request):    
        if 'floatingRows' not in request.session:
            request.session['floatingRows'] = []

        if 'headers' not in request.session or not request.session['headers']:
            request.session['headers'] = list(map(lambda x:x[0],self.fields))

        if "id" in request.POST:
            self.id = request.POST["id"]
            for field,entry in zip(request.session['headers'],request.session['floatingRows'][self.id]):
                self.form.fields[field] = entry        

        return render(request, 'dataedit/dataedit.html', {'form': self.form})

    def post(self, request):
        if 'headers' not in request.session:
            request.session['headers'] = list(map(lambda x:x[0],self.fields))
        # if this is a POST request we need to process the form data
        request.session.set_test_cookie()
        newRow = [request.POST[head] for head in request.session['headers']]
        print(self.id)
        if self.id:
            request.session['floatingRows'].insert(self.id,newRow) 
        else:
            request.session['floatingRows'].append(newRow)
        context = []
        
        return render(request,'dataedit/dataedit_overview.html',
            {'form': self.form, 'data':request.session['floatingRows'], 'headers':request.session['headers']})

class DataView(DBView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,*kwargs)

    
    def get(self, request):
        if 'floatingRows' not in request.session:
            request.session['floatingRows'] = []

        if 'headers' not in request.session or not request.session['headers']:
            request.session['headers'] = list(map(lambda x:x[0],self.fields))
      
        return render(request, 'dataedit/dataedit_overview.html', {'data':request.session['floatingRows'], 'headers':request.session['headers']})
    
    def post(self, request):
        view = DataInputView()

        if "id" in request.POST:
            view.id = int(request.POST["id"])
            for field,entry in zip(request.session['headers'],request.session['floatingRows'][view.id]):
                view.form.fields[field].initial = entry

        return render(request, 'dataedit/dataedit.html', {'form':view.form})        

class DataUploadView(DBView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,*kwargs)
        self.form = InputForm(fields=self.fields)

    def post(self,request):
        form = UploadFileForm(request.POST, request.FILES)
        print(form)
        if form.is_valid():
            #handle_uploaded_file(request.FILES['file'])
            return render(request, 'dataedit/dataedit_map.html', {'form':form})
        else:
            return render(request, 'dataedit/dataedit_upload.html', {'form':form})

    def get(self,request):
        form = UploadFileForm()
        return render(request,'dataedit/dataedit_upload.html', {'form': form})

class DataMapView(DBView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,*kwargs)
        self.form = InputForm(fields=self.fields)

    def post(self,request):
        def store(f):
            dname = 'tmp/'+f.name
            with open(dname, 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)
            return dname
        datafile = store(request.FILES['file'])
        with open(datafile,'r') as outf:
            reader = csv.reader(outf, delimiter='\t', quotechar='"')
            headers = next(reader)
            form = UploadMapForm(fields=self.fields,headers=headers)
        os.remove(datafile) #TODO: Unsicher!
        return render(request,'dataedit/dataedit_map.html', {'form': form})

    def get(self,request):
        def store(f):
            dname = 'tmp/'+f.name
            with open(dname, 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)
            return dname
        datafile = store(request.FILES['file'])
        with open(datafile,'r') as outf:
            reader = csv.reader(outf, delimiter='\t', quotechar='"')
            headers = next(reader)
            form = UploadMapForm(fields=self.fields,headers=headers)
        os.remove(datafile) #TODO: Unsicher!
        return render(request,'dataedit/dataedit_map.html', {'form': form})

    

def preserveform():
    def decorate(func):
        def call(*args, **kwargs):
            request = kwargs.pop('request')
            request.session['form'] = self.form
            func(*args, **kwargs)
            self.form = request.session['form']



