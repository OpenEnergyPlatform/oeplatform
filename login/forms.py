from captcha.fields import CaptchaField
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.forms import SetPasswordForm, UserChangeForm, UserCreationForm, PasswordChangeForm
from django.core.exceptions import ValidationError

from .models import UserGroup
from .models import myuser as OepUser


class CreateUserForm(UserCreationForm):
    captcha = CaptchaField()

    class Meta:
        model = OepUser
        fields = (
            "name",
            "email",
            "fullname",
            "location",
            "affiliation",
            "work",
            "linkedin",
            "twitter",
            "facebook",
            "profile_img",
            "password1",
            "password2",
        )

    def save(self, commit=True):
        user = super(CreateUserForm, self).save(commit=commit)
        user.send_activation_mail()
        return user

    def __init__(self, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)
        for key in self.Meta.fields:
            field = self.fields[key]
            cstring = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = cstring + "form-control"
            if field.required:
                field.label_suffix = "*"


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
            "email",
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


class DetachForm(SetPasswordForm):
    email = forms.EmailField(label="Mail")
    email2 = forms.EmailField(label="Mail confirmation")

    def clean_email(self):
        if not self.data["email"] == self.data["email2"]:
            raise ValidationError("The two email fields didn't match.")
        mail_user = OepUser.objects.filter(email=self.data["email"]).first()
        if mail_user and mail_user != self.user:
            raise ValidationError("This mail address is already in use.")

    def save(self, commit=True):
        super(DetachForm, self).save(commit=commit)
        self.user.email = self.data["email"]
        self.user.is_native = True
        self.user.is_mail_verified = False

        if commit:
            self.user.save()
            self.user.send_activation_mail()


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
        group_id = kwargs.pop(
            "group_id"
        )  # group_id is the parameter passed from views.py
        super(GroupUserForm, self).__init__(*args, **kwargs)
        if group_id != "":
            self.fields["groupmembers"].initial = OepUser.objects.filter(
                groups__id=group_id
            )
