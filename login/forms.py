from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.admin.widgets import FilteredSelectMultiple
from .models import myuser as OepUser, UserPermission
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, \
    PasswordChangeForm


class CreateUserForm(UserCreationForm):
    class Meta:
        model = OepUser
        fields = ('name', 'affiliation', 'mail_address', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)
        for key in self.Meta.fields:
            field = self.fields[key]
            cstring = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = cstring + 'form-control'
            if field.required:
                field.label_suffix = '*'

class EditUserForm(UserChangeForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """

    class Meta:
        model = OepUser
        fields = ('name', 'mail_address', 'affiliation', 'description')

    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        for key in self.Meta.fields:
            field = self.fields[key]
            cstring = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = cstring + 'form-control'
            if field.required:
                field.label_suffix = '*'

    def clean_password(self):
        return None


class GroupUserForm(forms.ModelForm):
    """
     A form for setting members of a group.     
    """
    class Meta:
        model = OepUser
        fields = ('groupmembers',)
    
    groupmembers = forms.ModelMultipleChoiceField(queryset=OepUser.objects,
                                                  widget=FilteredSelectMultiple("Members", is_stacked=False), 
                                                  required=False,)
    
    def __init__(self,*args,**kwargs):
        group_id = kwargs.pop("group_id")     # group_id is the parameter passed from views.py      
        super(GroupUserForm, self).__init__(*args,**kwargs)
        if group_id != "":
            self.fields['groupmembers'].initial = OepUser.objects.filter(groups__id=group_id)
