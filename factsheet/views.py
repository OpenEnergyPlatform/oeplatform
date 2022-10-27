from django.shortcuts import render

def factsheets_index(request, *args, **kwargs):
    return render(request, 'factsheet/index.html')
