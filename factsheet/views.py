from django.shortcuts import render
from django.http import Http404, HttpResponse, JsonResponse, StreamingHttpResponse
from rest_framework import status
from .models import Factsheet
import json
from django.views.decorators.csrf import csrf_exempt

def factsheets_index(request, *args, **kwargs):
    return render(request, 'factsheet/index.html')

@csrf_exempt
def create_factsheet(request, *args, **kwargs):
    name =request.GET.get('name')
    fs = Factsheet(factsheetData={'name': name})
    fs.save()
    return JsonResponse({'name': name}, status=status.HTTP_201_CREATED)

def factsheet_by_id(request, *args, **kwargs):
    return render(request, 'factsheet/index.html')
