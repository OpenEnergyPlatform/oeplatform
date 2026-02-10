"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Marco Finkendei <https://github.com/MFinkendei>
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from captcha.fields import CaptchaField
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.forms import PasswordChangeForm, UserChangeForm

from login.models import UserGroup
from login.models import myuser as OepUser


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """


class CreateUserForm(SignupForm):
    captcha = CaptchaField()

    def save(self, request):
        user = super(CreateUserForm, self).save(request)
        return user


class EditUserForm(UserChangeForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """

    # do NOT show the password field in the form
    password = None

    class Meta:
        model = OepUser
        fields = (
            "profile_img",
            # "email",
            "fullname",
            "location",
            "work",
            "linkedin",
            "twitter",
            "facebook",
            "affiliation",
            "description",
        )

    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        for key in self.Meta.fields:
            field = self.fields[key]
            cstring = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = cstring + "form-control"
            if field.required:
                field.label_suffix = "*"

    def clean_password(self):
        return None


class OEPPasswordChangeForm(PasswordChangeForm):
    captcha = CaptchaField()


class ChangeEmailForm(forms.Form):
    email = forms.EmailField()

    def save(self, user):
        user.email = self.cleaned_data["email"]
        user.save()
        user.send_activation_mail(reset_token=True)


class GroupForm(forms.ModelForm):
    class Meta:
        model = UserGroup
        fields = ("name", "description")


class GroupUserForm(forms.ModelForm):
    """
    A form for setting members of a group.
    """

    class Meta:
        model = OepUser
        fields = ("groupmembers",)

    groupmembers = forms.ModelMultipleChoiceField(
        queryset=OepUser.objects,
        widget=FilteredSelectMultiple("Members", is_stacked=False),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        # group_id is the parameter passed from views.py
        group_id = kwargs.pop("group_id")
        super(GroupUserForm, self).__init__(*args, **kwargs)
        if group_id != "":
            self.fields["groupmembers"].initial = OepUser.objects.filter(
                groups__id=group_id
            )
