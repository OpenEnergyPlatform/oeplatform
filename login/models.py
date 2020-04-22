import itertools
import json

import requests
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import (
    AbstractBaseUser,
    UserManager,
    Group,
    PermissionsMixin,
    User,
)
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

import dataedit.models as datamodels
import oeplatform.securitysettings as sec
from oeplatform.settings import METADATA_PERM_GROUP
from login.mail import send_verification_mail

NO_PERM = 0
WRITE_PERM = 4
DELETE_PERM = 8
ADMIN_PERM = 12


class OEPUserManager(UserManager):
    def create_user(self, name, email, affiliation=None):
        if not email:
            raise ValueError("An email address must be entered")
        if not name:
            raise ValueError("A name must be entered")

        user = self.model(
            name=name, email=self.normalize_email(email), affiliation=affiliation
        )

        user.save(using=self._db)
        user.send_activation_mail()
        return user

    def create_superuser(self, name, email, affiliation):

        user = self.create_user(name, email, affiliation=affiliation)
        user.is_admin = True
        user.save(using=self._db)
        return user

    def create_devuser(self, name, email):
        if not email:
            raise ValueError("An email address must be entered")
        if not name:
            raise ValueError("A name must be entered")
        user = self.model(
            name=name, email=self.normalize_email(email), affiliation=name, is_mail_verified=True
            )
        user.save(using=self._db)
        return user


class PermissionHolder:
    def has_write_permissions(self, schema, table):
        """
        This function returns the authorization given the schema and table.
        """
        return self.__get_perm(schema, table) >= WRITE_PERM

    def has_delete_permissions(self, schema, table):
        """
        This function returns the authorization given the schema and table.
        """
        return self.__get_perm(schema, table) >= DELETE_PERM

    def has_admin_permissions(self, schema, table):
        """
        This function returns the authorization given the schema and table.
        """
        return self.__get_perm(schema, table) >= ADMIN_PERM

    def __get_perm(self, schema, table):
        perm = self.table_permissions.filter(
            table__name=table, table__schema__name=schema
        ).first()
        if perm:
            return perm.level
        else:
            return NO_PERM


class UserGroup(Group, PermissionHolder):
    description = models.TextField(null=False, default="")
    is_admin = models.BooleanField(null=False, default=False)

    def get_table_permission_level(self, table):
        if self.is_admin:
            return ADMIN_PERM
        return max(
            itertools.chain(
                [NO_PERM],
                (perm.level for perm in self.table_permissions.filter(table=table)),
            )
        )


class TablePermission(models.Model):
    choices = (
        (NO_PERM, "None"),
        (WRITE_PERM, "Write"),
        (DELETE_PERM, "Delete"),
        (ADMIN_PERM, "Admin"),
    )
    table = models.ForeignKey(datamodels.Table, on_delete=models.CASCADE)

    level = models.IntegerField(choices=choices, default=NO_PERM)

    class Meta:
        unique_together = (("table", "holder"),)
        abstract = True


class myuser(AbstractBaseUser, PermissionHolder):
    name = models.CharField(max_length=50, unique=True)
    affiliation = models.CharField(max_length=50, blank=True)
    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)

    did_agree = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_mail_verified = models.BooleanField(default=False)

    is_admin = models.BooleanField(default=False)

    is_native = models.BooleanField(default=True)

    description = models.TextField(blank=True)

    USERNAME_FIELD = "name"

    REQUIRED_FIELDS = [name]

    objects = OEPUserManager()

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    def __str__(self):  # __unicode__ on Python 2
        return self.name

    @property
    def is_staff(self):
        return self.is_admin

    @property
    def is_reviewer(self):
        try:
            GroupMembership.objects.get(user=self, group__name=METADATA_PERM_GROUP)
        except GroupMembership.DoesNotExist:
            return False
        return True

    def get_table_permission_level(self, table):
        # Check admin permissions for user
        if self.is_admin:
            return ADMIN_PERM

        user_membership = self.table_permissions.filter(table=table).first()

        permission_level = NO_PERM
        if user_membership:
            permission_level = max(user_membership.level, permission_level)

        # Check permissions of all groups and choose least restrictive one
        group_perm_levels = (
            membership.group.get_table_permission_level(table)
            for membership in self.memberships.all()
        )

        if group_perm_levels:
            permission_level = max(
                itertools.chain([permission_level], group_perm_levels)
            )

        return permission_level

    def send_activation_mail(self, reset_token=False):
        token = self._generate_activation_code(reset_token=reset_token)
        send_verification_mail(self.email, token.value)

    def _generate_activation_code(self, reset_token=False):
        token = None
        if reset_token:
            ActivationToken.objects.filter(user=self).delete()
        else:
            token = ActivationToken.objects.filter(user=self).first()
        if not token:
            token = ActivationToken(user=self)
            candidate = PasswordResetTokenGenerator().make_token(self)
            # Make sure the token is unique
            while ActivationToken.objects.filter(value=candidate).first():
                candidate = PasswordResetTokenGenerator().make_token(self)
            token.value = candidate
            token.save()
        return token


class ActivationToken(models.Model):
    user = models.ForeignKey(myuser, on_delete=models.CASCADE)
    value = models.TextField()


class UserPermission(TablePermission):
    holder = models.ForeignKey(myuser, related_name="table_permissions", on_delete=models.CASCADE)


class GroupPermission(TablePermission):
    holder = models.ForeignKey(UserGroup, related_name="table_permissions", on_delete=models.CASCADE)


class GroupMembership(models.Model):
    choices = (
        (NO_PERM, "None"),
        (WRITE_PERM, "Invite"),
        (DELETE_PERM, "Remove"),
        (ADMIN_PERM, "Admin"),
    )
    user = models.ForeignKey(myuser, related_name="memberships", on_delete=models.CASCADE)
    group = models.ForeignKey(UserGroup, related_name="memberships", on_delete=models.CASCADE)
    level = models.IntegerField(choices=choices, default=WRITE_PERM)

    class Meta:
        unique_together = (("user", "group"),)


class UserBackend(object):
    def authenticate(self, username=None, password=None):
        """
        There are two possible means of authentication:

        1. If the user has registered via the OEP he can log in via his password
           and username.
        2. If the user is still connected to the openmod-wiki, the
           authentication falls back to this method.
        :param username:
        :param password:
        :return:
        """
        try:
            user = myuser.objects.get(name=username)
        except models.ObjectDoesNotExist:
            return None

        if user.is_native:
            if user.check_password(password):
                return user
            else:
                return None
        else:
            url = "https://wiki.openmod-initiative.org/api.php?action=login"
            data = {"format": "json", "lgname": username}

            # A first request to receive the required token
            token_req = requests.post(url, data)
            data["lgpassword"] = password
            data["lgtoken"] = token_req.json()["login"]["token"]

            # A second request for the actual authentication
            login_req = requests.post(url, data, cookies=token_req.cookies)

            if login_req.json()["login"]["result"] == "Success":
                return myuser.objects.get_or_create(name=username)[0]
            else:
                return None

    def get_user(self, user_id):
        try:
            return myuser.objects.get(pk=user_id)
        except myuser.DoesNotExist:
            return None


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
