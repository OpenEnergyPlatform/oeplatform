from django.shortcuts import render
from django.views.generic import View

# Create your views here.

class Welcome(View):
   
    def get(self, request):
        return render(request,'base/index.html',{}) 
