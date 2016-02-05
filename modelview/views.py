from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import View
from .models import Energymodel
from django.db.models import fields
from django.db import models
from oeplatform import settings
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
from .forms import EnergymodelForm

def listmodels(request):
    models = [(m.pk, m.full_name) for m in Energymodel.objects.all()]
    return render(request, "modelview/modellist.html", {'models':models})

def show(request, model_name):
    model = get_object_or_404(Energymodel, pk=model_name)
    user_agent = {'user-agent': 'oeplatform'}
    http = urllib3.PoolManager(headers=user_agent)
    org = None
    repo = None
    if model.github and model.link_to_source:
        match = re.match(r'.*github\.com\/(?P<org>[^\/]+)\/(?P<repo>[^\/]+)(\/.)*',model.link_to_source)
        org = match.group('org')
        repo = match.group('repo')
        gh_url = _handle_github_contributions(org,repo)
    return render(request,"modelview/model.html",{'model':model,'gh_org':org,'gh_repo':repo})

def editModel(request,model_name):
    model = get_object_or_404(Energymodel, pk=model_name)
    form = EnergymodelForm(instance=model)
    return render(request,"modelview/editmodel.html",{'form':form, 'name':model_name, 'method':'update'}) 
    
class ModelAdd(View):    
    def get(self,request):
        form = EnergymodelForm()
        return render(request,"modelview/editmodel.html",{'form':form, 'method':'add'})
    def post(self,request):
        form = EnergymodelForm(request.POST or None)
        if form.is_valid():
            form.save()
            model_name = request.POST["id_name"]
            return redirect("/models/{model}".format(model=model_name))
        return render(request,"modelview/editmodel.html",{'form':form, 'method':'add'})

def updateModel(request,model_name):
    model = get_object_or_404(Energymodel, pk=model_name)
    form = EnergymodelForm(request.POST or None, instance=model)
    if form.is_valid():
        form.save()
        return redirect("/models/{model}".format(model=model_name))
    return render(request,"modelview/editmodel.html",{'form':form, 'name':model_name})

"""
    This function returns the url of an image of recent GitHub contributions
    If the image is not present or outdated it will be reconstructed
"""
def _handle_github_contributions(org,repo, timedelta=3600, weeks_back=8):
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
            print("Could not load GitHub statistics")
        
        reply = json.loads(reply)
        
        if not reply:
            return None

        print(reply)
        # If there are more weeks than nessecary, truncate
        if weeks_back < len(reply):
            reply = reply[-weeks_back:]
        print(reply)    
        # GitHub API returns a JSON dict with w: weeks, c: contributions
        (times, commits)=zip(*[(datetime.datetime.fromtimestamp(
                int(week['week'])
            ).strftime('%m-%d'), sum(map(int,week["days"]))) for week in reply])
        max_c = max(commits)
        
        # generate a distribution wrt. to the commit numbers
        commits_ids = [i  for i in range(len(commits)) for _ in range(commits[i])]
        print(commits_ids)
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
