from django.shortcuts import get_object_or_404, render, redirect,\
    render_to_response
from django.views.generic import View
from django.views.generic.edit import UpdateView
from .models import myuser as OepUser, GroupMembership, ADMIN_PERM, UserGroup
from .forms import CreateUserForm, EditUserForm, DetachForm
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
import login.models as models
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth import update_session_auth_hash

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
        return render(request, "login/profile.html", {'profile_user': user,
                                                      'token': token})

class GroupManagement(View, LoginRequiredMixin):
    def get(self, request):
        """
        Load and list the available groups by groupadmin. 
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :return: Profile renderer   
        """

        membership = request.user.memberships
        return render(request, "login/list_memberships.html", {'membership': membership})


class GroupCreate(View, LoginRequiredMixin):
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
            membership = get_object_or_404(GroupMembership, group=group,
                                           user=request.user)
            if membership.level < ADMIN_PERM:
                raise PermissionDenied
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
                raise PermissionDenied
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
        return redirect('/user/groups/{id}/members'.format(id=group.id))

class GroupEdit(View, LoginRequiredMixin):
    def get(self, request, group_id):
        """
        Load the chosen action(create or edit) for a group. 
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :param user_id: An group id
        :return: Profile renderer   
        """
        group = get_object_or_404(UserGroup, pk=group_id)
        is_admin = False
        membership = GroupMembership.objects.filter(group=group, user=request.user).first()
        if membership:
            is_admin = membership.level >= ADMIN_PERM
        return render(request, "login/change_form.html", {'group': group,
                                                          'choices': GroupMembership.choices,
                                                          'is_admin': is_admin})
        
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
        membership = get_object_or_404(GroupMembership, group=group,
                                       user=request.user)

        errors = {}
        if mode == 'add_user':
            if membership.level < models.WRITE_PERM:
                raise PermissionDenied
            try:
                user = OepUser.objects.get(name=request.POST['name'])
                membership, _ = GroupMembership.objects.get_or_create(group=group,
                                                                      user=user)
                membership.save()
            except OepUser.DoesNotExist:
                errors['name'] = 'User does not exist'
        elif mode == 'remove_user':
            if membership.level < models.DELETE_PERM:
                raise PermissionDenied
            user = OepUser.objects.get(id=request.POST['user_id'])
            membership = GroupMembership.objects.get(group=group,
                                                     user=user)
            if membership.level >= ADMIN_PERM:
                admins = GroupMembership.objects.filter(group=group).exclude(user=user)
                if not admins:
                    errors['name'] = 'A group needs at least one admin'
                else:
                    membership.delete()
            else:
                membership.delete()
        elif mode == 'alter_user':
            if membership.level < models.ADMIN_PERM:
                raise PermissionDenied
            user = OepUser.objects.get(id=request.POST['user_id'])
            if user == request.user:
                errors['name'] = 'You can not change your own permissions'
            else:
                membership = GroupMembership.objects.get(group=group,
                                                         user=user)
                membership.level = request.POST['level']
                membership.save()
        elif mode == 'delete_group':
            if membership.level < models.ADMIN_PERM:
                raise PermissionDenied
            group.delete()
            return redirect('/user/groups')
        else:
            raise PermissionDenied
        return render(request, "login/change_form.html", {'group': group,
                                                          'choices': GroupMembership.choices,
                                                          'errors': errors,
                                                          'is_admin': True})

    def __add_user(self, request, group):
        user = OepUser.objects.filter(id=request.POST['user_id']).first()
        g = user.groups.add(group)
        g.save()
        return self.get(request)

class ProfileUpdateView(UpdateView, LoginRequiredMixin):
    """
    Autogenerate a update form for users.
    """
    model = OepUser
    fields = ['name','affiliation','mail_address']
    template_name_suffix = '_update_form'


class EditUserView(View):
    def get(self, request, user_id):
        if not request.user.id == int(user_id):
            raise PermissionDenied
        form = EditUserForm(instance=request.user)
        return render(request, 'login/oepuser_edit_form.html', {'form': form})

    def post(self, request, user_id):
        if not request.user.id == int(user_id):
            raise PermissionDenied
        form = EditUserForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('/user/profile/{id}'.format(id=request.user.id))
        else:
            return render(request, 'login/oepuser_edit_form.html',
                          {'form': form})

class CreateUserView(View):
    def get(self, request):
        form = CreateUserForm()
        return render(request, 'login/oepuser_create_form.html', {'form': form})

    def post(self, request):
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Mark that the user does not use any external means of authentication
            user.is_native = True
            user.save()
            return redirect('/user/profile/{id}'.format(id=user.id))
        else:
            return render(request, 'login/oepuser_create_form.html',
                          {'form': form})


class DetachView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_native:
            raise PermissionDenied
        form = DetachForm(request.user)
        return render(request, 'login/detach.html', {'form': form})

    def post(self, request):
        if request.user.is_native:
            raise PermissionDenied
        form = DetachForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')
        else:
            print(form.errors)
            return render(request, 'login/detach.html', {'form': form})

class OEPPasswordChangeView(PasswordChangeView):
    template_name = 'login/generic_form.html'