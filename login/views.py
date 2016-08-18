from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import View
from django.views.generic.edit import UpdateView
from .models import OepUser

class ProfileView(View):
    def get(self, request, user_id):
        user = get_object_or_404(OepUser, pk=user_id)
        return render(request, "login/profile.html", {'user':user})

class ProfileUpdateView(UpdateView):
    model = OepUser
    fields = ['name','affiliation','mail_address']
    template_name_suffix = '_update_form'

def create_user(request):
    return redirect(request, "http://wiki.openmod-initiative.org/wiki/Special:RequestAccount")

