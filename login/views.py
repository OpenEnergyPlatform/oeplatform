from django.shortcuts import get_object_or_404, render, redirect,\
    render_to_response
from django.views.generic import View
from django.views.generic.edit import UpdateView
from .models import myuser as OepUser
from .forms import AllPermForm, GroupUserForm
from django.contrib.auth.models import Group

 

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
        """
        Load and list the available groups by groupadmin. 
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :return: Profile renderer   
        """
        user = get_object_or_404(OepUser, pk=user_id)
        groups = user.groupadmin.all()       
        return render(request, "login/admin_group.html", {'user': user, 'groupresult': groups})
    
class GroupEdit(View):
    def get(self, request, user_id, group_id=""):
        """
        Load the chosen action(create or edit) for a group. 
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :param user_id: An group id
        :return: Profile renderer   
        """
        user = get_object_or_404(OepUser, pk=user_id)
        members = GroupUserForm(group_id=group_id)
        if group_id != "":
            group = get_object_or_404(Group, pk=group_id)
            form = AllPermForm(user = user, group = group)
            form.label = group.name
            return render(request, "login/change_form.html", {'user': user, 'group_id': group_id, 'form': form, 'members':members})    
        form = AllPermForm(user = user, group = "")
        return render(request, "login/change_form.html", {'user': user, 'form': form, 'members':members})
        
    def post(self, request, user_id, group_id=""):
        """
        Performs selected action(save or delete) for a group. If a groupname already exists, then a error 
        will be output. 
        The selected users become members of this group. The groupadmin is already set.
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :param user_id: An group id
        :return: Profile renderer   
        """
        user = get_object_or_404(OepUser, pk=user_id)
        if group_id != "":
            group = get_object_or_404(Group, pk=group_id)
            form = AllPermForm(request.POST, user = user, group = group)
        else:
            form = AllPermForm(request.POST, user = user, group = "")
        form.label = request.POST["group_name"]
        members = GroupUserForm(request.POST, group_id=group_id)

        if form.is_valid() and members.is_valid():
            groupperms = form.cleaned_data.get('allperms')
            groupuser = members.cleaned_data.get('groupmembers')
            
            if "Save" in request.POST["submit"]:
                if group_id != "":
                    if groupperms == None:
                        group.permissions.clear()
                    else:
                        group.permissions.set(groupperms)
                    _set_group_members(user=user, group=group, groupuser=groupuser)                 
                    Group.objects.filter(id = group_id).update(name = form.label)
                else:
                    if Group.objects.filter(name = form.label).exists():
                        error = "Groupname already exists! Chose another name. "
                        return render(request, "login/change_form.html", {'user': user, 'form': form, 'error': error})
                    
                    group = Group.objects.create(name = form.label)
                    if groupperms != None:
                        group.permissions.set(groupperms)
                    user.groupadmin.add(group)
                    _set_group_members(user=user, group=group, groupuser=groupuser)
                   
            elif "Delete" in request.POST["submit"]:
                group.permissions.clear()
                user.groupadmin.remove(group)
                Group.objects.filter(id = group_id).delete()

        groups = user.groupadmin.all()  
        return render(request, "login/admin_group.html", {'user': user, 'groupresult': groups})

def _set_group_members(user, group, groupuser):
    """
    Help function for EditGroups. This set the selected users to the group.
    """ 
    group.user_set.clear()
    group.user_set.set(groupuser)
    user.groups.add(group)

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

