from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import View
from .models import myuser
from .forms import UserCreationForm

class ProfileView(View):
    def get(self, request, user_id):
        user = get_object_or_404(myuser, name=user_id)
        return render(request, "login/profile.html", {'user':user})
        
class CreateProfileView(View):
    def get(self, request):
        form = UserCreationForm()
        return render(request, "registration/createuser.html", {'form':form})
        
    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            id = request.POST["name"]
            return redirect("login/profile/{name}.html".format(name=name))
        else:
            return render(request, "registration/createuser.html", {'form':form})
