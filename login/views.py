from django.shortcuts import get_object_or_404, render, redirect,\
    render_to_response
from django.views.generic import View
from django.views.generic.edit import UpdateView
from .models import myuser as OepUser
from rest_framework.authtoken.models import Token
from django.template.context import RequestContext
from .forms import GroupPermForm
from django.contrib.admin.helpers import Fieldset


class ProfileView(View):
    def get(self, request, user_id):
        """
        Load the user identified by user_id and is OAuth-token. If latter does not exist yet, create one.
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :return: Profile renderer
        """
        from rest_framework.authtoken.models import Token
        for user in OepUser.objects.all():
            Token.objects.get_or_create(user=user)
        user = get_object_or_404(OepUser, pk=user_id)
        token = None
        if request.user.is_authenticated:
            token = Token.objects.get(user=request.user)
        return render(request, "login/profile.html", {'user': user,
                                                      'token': token})

class GroupManagement(View):
    def get(self, request, user_id):
        user = get_object_or_404(OepUser, pk=user_id)
        perm = user.get_writeable_tables()
        return render(request, "login/admin_group.html", {'user': user, 'perm': perm})
    
class GroupEdit(View):
    def get(self, request, user_id):
        user = get_object_or_404(OepUser, pk=user_id)
        perm = user.get_writeable_tables()
        form = GroupPermForm(user = user)
        fieldsets = (
                     Fieldset(form,'Available',),
                     Fieldset(form,'Chosen',),
                     )
        return render(request, "login/change_form.html", {'user': user, 'perm': perm, 'form': form, 'fieldsets': fieldsets})
    
    def post(selfself, request, user_id):
        user = get_object_or_404(OepUser, pk=user_id)
        perm = user.get_writeable_tables()
        form = GroupPermForm(request.POST, user= user)
        if form.is_valid():
            groupperms = form.cleaned_data.get('groupperms')
            # do something with your results
            fieldsets = (
                     Fieldset(form,'Available',),
                     Fieldset(form,'Chosen',),
                     )
        return render(request, "login/change_form.html", {'user': user, 'perm': perm, 'form': form, 'fieldsets': fieldsets})
    
class ProfileUpdateView(UpdateView):
    """
    Autogenerate a update form for users.
    """
    model = OepUser
    fields = ['name','affiliation','mail_address']
    template_name_suffix = '_update_form'


def create_user(request):
    """
    We use the user management implemented in the wiki of the openMod-community.
    New users must be created there.
    :param request: A HTTP-request object sent by the Django framework.
    :return: Redirect to AccountRequest-form on wiki.openmod-initiative.org
    """
    return redirect(request, "http://wiki.openmod-initiative.org/wiki/Special:RequestAccount")

