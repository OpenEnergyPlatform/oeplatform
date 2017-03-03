from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.admin.widgets import FilteredSelectMultiple
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

class GroupUserForm(forms.ModelForm):
    """
     A form for setting members of a group.     
    """
    class Meta:
        model = OepUser
        fields = ('groupmembers',)
    
    groupmembers = forms.ModelMultipleChoiceField(queryset=OepUser.objects.filter(is_superuser=False).filter(is_admin=False), 
                                                  widget=FilteredSelectMultiple("Members", is_stacked=False), 
                                                  required=False,)
    
    def __init__(self,*args,**kwargs):
        group_id = kwargs.pop("group_id")     # group_id is the parameter passed from views.py      
        super(GroupUserForm, self).__init__(*args,**kwargs)
        if group_id != "":
            self.fields['groupmembers'].initial = OepUser.objects.filter(groups__id=group_id)

class AllPermForm(forms.ModelForm):
    """
     A form for create/edit permissions of a group.   
    """
    class Meta:
        model = OepUser
        fields =('allperms',)
    allperms = forms.ModelMultipleChoiceField(queryset="", 
                                              widget=FilteredSelectMultiple("Permissions", is_stacked=False), 
                                              required=False,)
    
    def __init__(self,*args,**kwargs):
        user = kwargs.pop("user")
        group = kwargs.pop("group")     # user is the parameter passed from views.py
        super(AllPermForm, self).__init__(*args,**kwargs)
        self.fields['allperms'] = forms.ModelMultipleChoiceField(queryset=user.get_all_avail_perms(),
                                                                 widget=FilteredSelectMultiple("Permissions", 
                                                                 is_stacked=False),
                                                                 required=False,)
        if group != "":
            self.fields['allperms'].initial = group.permissions.all()
        
        