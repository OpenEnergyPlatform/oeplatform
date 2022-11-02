from django.shortcuts import render
import json

def factsheets_index(request, *args, **kwargs):
    return render(request, 'factsheet/index.html')
