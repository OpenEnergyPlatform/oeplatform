from django.shortcuts import render

def factsheets_index(request, *args, **kwargs):
    return render(request, 'build/index.html')
