from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import myuser as OepUser



class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = OepUser
        fields = ('name', 'affiliation', 'mail_address')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]

class GroupPermForm(forms.Form):
    def __init__(self,*args,**kwargs):
        user = kwargs.pop("user")     # user is the parameter passed from views.py
        super(GroupPermForm, self).__init__(*args,**kwargs)
        OPTIONS = (
                (1, "ADD"),
                (2, "EDIT"),
                (3, "REMOVE"),
                )
        #perm_data = Permission.objects.filter(content_type_id=102)
        group = user.groupadmin.get()
        perm_data = group.permissions.all()
        OPTIONS =[((choice.id), (choice)) for choice in perm_data]
        self.fields['groupperms'] = forms.MultipleChoiceField(widget=forms.SelectMultiple(attrs={'class': 'selectfilter'}), label = '', choices=OPTIONS)