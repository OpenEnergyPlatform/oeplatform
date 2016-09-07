from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import View
from django.views.generic.edit import UpdateView
from .models import myuser as OepUser
from rest_framework.authtoken.models import Token

class ProfileView(View):
    def get(self, request, user_id):
        from rest_framework.authtoken.models import Token
        for user in OepUser.objects.all():
            Token.objects.get_or_create(user=user)
        user = get_object_or_404(OepUser, pk=user_id)
        token = None
        if request.user.is_authenticated:
            token = Token.objects.get(user=request.user)
        return render(request, "login/profile.html", {'user': user,
                                                      'token': token})

class ProfileUpdateView(UpdateView):
    model = OepUser
    fields = ['name','affiliation','mail_address']
    template_name_suffix = '_update_form'

def create_user(request):
    return redirect(request, "http://wiki.openmod-initiative.org/wiki/Special:RequestAccount")

