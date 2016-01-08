from django.shortcuts import render
from django.views.generic import View

# Create your views here.

class Welcome(View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,*kwargs)

    
    def get(self, request):
        return render(request,'base/index.html',{}) 
