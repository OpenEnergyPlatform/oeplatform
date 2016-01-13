from django.shortcuts import get_object_or_404, render
from django.views.generic import View
from .models import Energymodel
from django.db.models import fields
from django.db import models
from oeplatform import settings
# Create your views here.

class ModelView(View):
    def get(self, request, model_name):
        model = get_object_or_404(Energymodel, pk=model_name)
        """for field in model._meta.fields:
            if type(field) == fields.CharField:
                print("<tr><td> {0}:</td><td> {{{{ model.{0} }}}}</td></tr>".format(field.name))
            elif type(field) == fields.BooleanField:
                    print('<tr><td> {0}:</td><td> {{% if model.{0} %}} {{% bootstrap_icon "ok" %}} {{% else %}} {{% bootstrap_icon "remove" %}} {{% endif %}}</td></tr>'.format(field.name))
            elif type(field) == models.ImageField:
                print('<tr><td> {0}:</td><td> <img src={{{{ model.{0}.url }}}} style="width:200"/></td></tr>'.format(field.name, field.name))
            else:
                print("<tr><td> {0}:</td><td> {{{{ model.{0} }}}}</td></tr>".format(field.name))"""
        return render(request,"modelview/model.html",{'model':model})
