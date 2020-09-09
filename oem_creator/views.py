
from django.views.generic import TemplateView

from oem_creator.forms import CreatorForm

from django.views.generic.base import TemplateView
from django.views.generic import ListView
from .forms import CreatorForm
from django.shortcuts import render




class CreatorView(TemplateView):
    template_name = 'meta_creator/creator.html'

    def get_context_data(self, **kwargs):
        return {'form': CreatorForm()}


# Create your views here.
def home_view(request):
    print(request.GET)
    return render(request, "meta_creator/creator.html")