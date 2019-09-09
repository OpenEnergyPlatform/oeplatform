from django.shortcuts import render


def tutorial_home(request):
    return render(request, 'tutorial/tutorial_home.html')

def database_conform_data(request):
    return render(request, 'tutorial/database_conform_data.html')