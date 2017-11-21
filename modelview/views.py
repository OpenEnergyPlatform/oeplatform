from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import View
from django.db.models import fields
from django.db import models
import django.forms as forms
from oeplatform import settings
from dataedit.structures import Tag
from api.actions import _get_engine
from django.contrib.staticfiles.templatetags.staticfiles import static
# Create your views here.
import matplotlib.pyplot as plt
import urllib3
import json
import datetime
from scipy import stats
import numpy 
import os
from django.conf import settings as djangoSettings
from matplotlib.lines import Line2D
import matplotlib
import time
import re
from .models import Energymodel, Energyframework, Energyscenario, Energystudy
from .forms import EnergymodelForm, EnergyframeworkForm, EnergyscenarioForm, EnergystudyForm
from django.contrib.postgres.fields import ArrayField

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from sqlalchemy.orm import sessionmaker

from sqlalchemy.dialects.postgresql import array_agg
def getClasses(sheettype):
    """
    Returns the model and form class w.r.t sheettype.
    """
    if sheettype == "model":
        c = Energymodel
        f = EnergymodelForm
    elif sheettype == "framework":
        c = Energyframework
        f = EnergyframeworkForm
    elif sheettype == "scenario":
        c = Energyscenario
        f = EnergyscenarioForm
    elif sheettype == "studie":
        c = Energystudy
        f = EnergystudyForm
    return c,f
     

def overview(request):
    return render(request, "modelview/overview.html",)

def load_tags():
    engine = _get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    tags = list(session.query(Tag))
    d = {tag.id: tag for tag in tags}
    session.close()
    return d

def listsheets(request,sheettype):
    """
    Lists all available model, framework or scenario factsheet objects.
    """
    c,_ = getClasses(sheettype)
    tags = []
    if sheettype == "scenario":
        models = [(m.pk, m.name_of_scenario) for m in c.objects.all()]
    elif sheettype == "studie":
        models = [(m.pk, m.name_of_the_study) for m in c.objects.all()]
    else:
        d = load_tags()
        models = []
        for model in c.objects.all():
            model.tags = [d[tag_id] for tag_id in model.tags]
            models.append(model)
    if sheettype == 'scenario':
        label='Scenario'
    elif sheettype == 'studie':
        label='Study'
    elif sheettype == 'framework':
        label='Framework'
    else:
        label='Model'
    return render(request, "modelview/modellist.html", {'models':models, 'label':label, 'tags':tags})

def show(request, sheettype, model_name):
    """
    Loads the requested factsheet
    """
    c,_ = getClasses(sheettype)
    model = get_object_or_404(c, pk=model_name)
    model_study=[]
    if sheettype == "scenario":
        c_study,_ = getClasses("studie")
        model_study = get_object_or_404(c_study, pk=model.study.pk)
    else:
        d = load_tags()
        model.tags = [{'id': d[tag_id].id, 'name': d[tag_id].name, 'color': "#" + format(d[tag_id].color, '06X')} for tag_id in model.tags]

    user_agent = {'user-agent': 'oeplatform'}
    http = urllib3.PoolManager(headers=user_agent)
    org = None
    repo = None
    if sheettype != "scenario" and sheettype !="studie":
        if model.gitHub and model.link_to_source_code:
            try:
                match = re.match(r'.*github\.com\/(?P<org>[^\/]+)\/(?P<repo>[^\/]+)(\/.)*',model.link_to_source_code)
                org = match.group('org')
                repo = match.group('repo')
                gh_url = _handle_github_contributions(org,repo)
            except:
                org = None
                repo = None
    return render(request,("modelview/{0}.html".format(sheettype)),{'model':model,'model_study':model_study,'gh_org':org,'gh_repo':repo})
    

def set_tags(request, sheettype, model_name, ):
    """
    Loads the requested factsheet
    """
    c,_ = getClasses(sheettype)
    model = get_object_or_404(c, pk=model_name)

    ids = {int(field[len('tag_'):]) for field in request.POST if
           field.startswith('tag_')}

    if sheettype == "scenario":
        raise NotImplementedError
    else:
        model.tags = sorted(list(ids))
        model.save()

    return redirect(request.META['HTTP_REFERER'])

def processPost(post, c, f, files=None, pk=None, key=None):
    """
    Returns the form according to a post request
    """
    fields = {k:post[k] for k in post}
    if 'new' in fields and fields['new']=='True':
        fields['study']=key
    for field in c._meta.get_fields():
        if type(field) == ArrayField:
            parts = []
            for fi in fields.keys():
                if re.match("^{}_\d$".format(field.name),str(fi)) and fields[fi]:
                    parts.append(fi)
            parts.sort()
            fields[field.name]= ",".join(fields[k].replace(",",";") for k in parts)
            for fi in parts:
                del(fields[fi])
        else:
            if field.name in fields:
                fields[field.name] = fields[field.name]
    if pk:
        model = get_object_or_404(c, pk=pk)
        return f(fields,files,instance=model)
    else: 
        return f(fields,files)     
    
    
@login_required
def editModel(request,model_name, sheettype):
    """
    Constructs a form accoring to existing model
    """
    c,f = getClasses(sheettype) 
        
    model = get_object_or_404(c, pk=model_name)

    tags = []
    if sheettype == "scenario":
        pass
    else:
        d = load_tags()
        tags = [{'id': d[tag_id].id, 'name': d[tag_id].name, 'color': "#" + format(d[tag_id].color, '06X')} for tag_id in model.tags]

    form = f(instance=model)
    
    return render(request,"modelview/edit{}.html".format(sheettype),{'form':form, 'name':model_name, 'method':'update', 'tags': tags})

class FSAdd(LoginRequiredMixin, View):
    def get(self,request, sheettype, method='add'):
        c,f = getClasses(sheettype) 
        if method == 'add':
            form = f()
            if sheettype =='scenario':
                c_study,f_study = getClasses('studie')
                formstudy = f_study()
                return render(request,"modelview/new{}.html".format(sheettype),{'form':form, 'formstudy':formstudy, 'method':method})
            else:
                return render(request,"modelview/edit{}.html".format(sheettype),{'form':form, 'method':method})
        else:
            model = get_object_or_404(c, pk=model_name)
            form = f(instance=model)
            return render(request,"modelview/edit{}.html".format(sheettype),{'form':form, 'name':model.pk, 'method':method})
    
    def post(self,request, sheettype, method='add', pk=None):
        c,f = getClasses(sheettype)
        form = processPost(request.POST,  c, f, files=request.FILES, pk=pk)
        if sheettype =='scenario' and method=='add':
            c_study,f_study = getClasses('studie')
            formstudy = processPost(request.POST,  c_study, f_study, files=request.FILES, pk=pk)
            errorsStudy=[]
            if request.POST['new'] == 'True':
                if formstudy.is_valid():
                    n=formstudy.save()
                    form = processPost(request.POST,  c, f, files=request.FILES, pk=pk, key=n.pk)
                else:
                    errorsStudy = [(field.label, str(field.errors.data[0].message)) for field in formstudy if field.errors]
            if form.is_valid() and errorsStudy==[]:
                m = form.save()
                return redirect("/factsheets/{sheettype}s/{model}".format(sheettype=sheettype,model=m.pk))
            else:
                errors = [(field.label, str(field.errors.data[0].message)) for field in form if field.errors]+errorsStudy
                return render(request,"modelview/new{}.html".format(sheettype),{'form':form, 'formstudy':formstudy, 'name':pk, 'method':method, 'errors':errors})
        else:
            if form.is_valid():
                m = form.save()
                return redirect("/factsheets/{sheettype}s/{model}".format(sheettype=sheettype,model=m.pk))
            else:
                errors = [(field.label, str(field.errors.data[0].message)) for field in form if field.errors]
                return render(request,"modelview/edit{}.html".format(sheettype),{'form':form, 'name':pk, 'method':method, 'errors':errors})



def _handle_github_contributions(org,repo, timedelta=3600, weeks_back=8):
    """
    This function returns the url of an image of recent GitHub contributions
    If the image is not present or outdated it will be reconstructed
    """
    path = "GitHub_{0}_{1}_Contribution.png".format(org,repo)
    full_path = os.path.join(djangoSettings.MEDIA_ROOT,path)

    # Is the image already there and actual enough?
    if False:#os.path.exists(full_path) and int(time.time())-os.path.getmtime(full_path) < timedelta:
        return static(path)
    else:
        # We have to replot the image
        # Set plot font
        font = {'family' : 'normal'}
        matplotlib.rc('font', **font)        
        
        # Query GitHub API for contributions
        user_agent = {'user-agent': 'oeplatform'}
        http = urllib3.PoolManager(headers=user_agent)
        try:
            reply = http.request("GET","https://api.github.com/repos/{0}/{1}/stats/commit_activity".format(org,repo)).data.decode('utf8')
        except:
            pass
        
        reply = json.loads(reply)
        
        if not reply:
            return None

        # If there are more weeks than nessecary, truncate
        if weeks_back < len(reply):
            reply = reply[-weeks_back:]
 
        # GitHub API returns a JSON dict with w: weeks, c: contributions
        (times, commits)=zip(*[(datetime.datetime.fromtimestamp(
                int(week['week'])
            ).strftime('%m-%d'), sum(map(int,week["days"]))) for week in reply])
        max_c = max(commits)
        
        # generate a distribution wrt. to the commit numbers
        commits_ids = [i  for i in range(len(commits)) for _ in range(commits[i])]

        # transform the contribution distribution into a density function
        # using a gaussian kernel estimator
        if commits_ids:        
            density = stats.kde.gaussian_kde(commits_ids, bw_method=0.2)
        else:
            # if there are no commits the density is a constant 0
            density = lambda x:0
        # plot this distribution
        x = numpy.arange(0., len(commits),.01)
        c_real_max = max(density(xv) for xv in x) 
        fig1 = plt.figure(figsize=(4, 2))  #facecolor='white',     
        
        # replace labels by dates and numbers of commits
        ax1 = plt.axes(frameon=False)
        plt.fill_between(x, density(x),0)
        ax1.set_frame_on(False)
        ax1.axes.get_xaxis().tick_bottom()
        ax1.axes.get_yaxis().tick_left()
        plt.yticks(numpy.arange(c_real_max-0.001,c_real_max), 
                                [max_c], 
                                size='small')
        plt.xticks(numpy.arange(0.,len(times)), times, size='small',rotation=45)
        
        # save the figure
        plt.savefig(full_path, transparent=True, bbox_inches='tight')
        url = static(path)
        return url
