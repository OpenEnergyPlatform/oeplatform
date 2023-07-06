from django.shortcuts import render

def viewer_index(request, *args, **kwargs):
    return render(request, "index.html")
