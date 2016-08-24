from django.shortcuts import render
from api import actions
from django.http import HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django_ajax.decorators import ajax
import json
import time

def date_handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        return str(obj)


# Create your views here.


def create_ajax_handler(func):
    @ajax
    @csrf_exempt
    def execute(request):
        content = request.POST if request.POST else request.GET
        data = func(json.loads(content['query']))

        # This must be done in order to clean the structure of non-serializable
        # objects (e.g. datetime)
        return json.loads(json.dumps(data, default=date_handler))
    return execute


def stream(data):
    size = len(data)
    chunck = 100

    for i in range(size):
        yield json.loads(json.dumps(data[i], default=date_handler))
        time.sleep(1)