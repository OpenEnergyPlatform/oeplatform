from django.shortcuts import get_object_or_404, render, redirect,\
    render_to_response
from django.views.generic import View
from django.views.generic.edit import UpdateView
from .models import myuser as OepUser, GroupMembership, ADMIN_PERM, UserGroup
from .forms import GroupUserForm
from django.contrib.auth.models import Group
from django.http import HttpResponseForbidden

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
    def get(self, request):
        """
        Load and list the available groups by groupadmin. 
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :return: Profile renderer   
        """

        membership = request.user.memberships
        return render(request, "login/list_memberships.html", {'membership': membership})


class GroupCreate(View):
    def get(self, request, group_id=None):
        """
        Load the chosen action(create or edit) for a group.
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :param user_id: An group id
        :return: Profile renderer
        """
        group = None
        if group_id:
            group = UserGroup.objects.get(id=group_id)
        return render(request, "login/group_create.html", {'group': group})

    def post(self, request, group_id=None):
        """
        Performs selected action(save or delete) for a group. If a groupname already exists, then a error
        will be output.
        The selected users become members of this group. The groupadmin is already set.
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :param user_id: An group id
        :return: Profile renderer
        """

        if group_id:
            group = UserGroup.objects.get(id=group_id)
            membership = get_object_or_404(GroupMembership, group=group, user=request.user)
            if membership.level < ADMIN_PERM:
                return HttpResponseForbidden()
            group.name = request.POST['name']
            group.description = request.POST['description']
            group.save()
        else:
            group = UserGroup.objects.create(name=request.POST['name'])
            group.save()
            membership = GroupMembership.objects.create(user=request.user,
                                                        group=group,
                                                        level=ADMIN_PERM)
            membership.save()
        return render(request, "login/change_form.html", {'group': group,
                                                          'choices': GroupMembership.choices})

class GroupEdit(View):
    def get(self, request, group_id):
        """
        Load the chosen action(create or edit) for a group. 
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :param user_id: An group id
        :return: Profile renderer   
        """
        group = get_object_or_404(UserGroup, pk=group_id)
        return render(request, "login/change_form.html", {'group': group,
                                                          'choices': GroupMembership.choices})
        
    def post(self, request, group_id):
        """
        Performs selected action(save or delete) for a group. If a groupname already exists, then a error 
        will be output. 
        The selected users become members of this group. The groupadmin is already set.
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :param user_id: An group id
        :return: Profile renderer   
        """
        mode = request.POST['mode']
        group = get_object_or_404(UserGroup, id=group_id)
        errors = {}
        if mode == 'add_user':
            try:
                user = OepUser.objects.get(name=request.POST['name'])
                membership = GroupMembership.objects.create(group=group,
                                                            user=user,
                                                            level=ADMIN_PERM)
                membership.save()
            except OepUser.DoesNotExist:
                errors['name'] = 'User does not exist'
        elif mode == 'remove_user':
            user = OepUser.objects.get(id=request.POST['user_id'])
            GroupMembership.objects.remove(group=group,
                                           user=user)
        elif mode == 'alter_user':
            user = OepUser.objects.get(id=request.POST['user_id'])
            membership = GroupMembership.objects.get(group=group,
                                                     user=user)
            membership.level = request.POST['level']
            membership.save()

        return render(request, "login/change_form.html", {'group': group,
                                                          'choices': GroupMembership.choices,
                                                          'errors': errors})

    def __add_user(self, request, group):
        user = OepUser.objects.filter(id=request.POST['user_id']).first()
        g = user.groups.add(group)
        g.save()
        return self.get(request)

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

