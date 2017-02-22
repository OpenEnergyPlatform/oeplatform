from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
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
    OPTIONS = (
            (1, "ADD"),
            (2, "EDIT"),
            (3, "REMOVE"),
            )
    groupperms = forms.MultipleChoiceField(widget=forms.SelectMultiple, label = '', choices=OPTIONS)