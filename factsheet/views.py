from django.shortcuts import render

def factsheets_index(request, *args, **kwargs):
    context_dict = {
        "user": 'Adel',
    }
    return render(request, 'factsheet/index.html', context='context')
