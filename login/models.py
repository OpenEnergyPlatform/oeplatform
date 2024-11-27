import itertools

import requests
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, Group, UserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

import dataedit.models as datamodels

try:
    import oeplatform.securitysettings as sec  # noqa
except Exception:
    import logging

    logging.error("No securitysettings found. Triggerd in login/models.py")


NO_PERM = 0
WRITE_PERM = 4
DELETE_PERM = 8
ADMIN_PERM = 12


class OEPUserManager(UserManager):
    def create_user(
        self,
        name,
        email,
        affiliation=None,
        profile_img=None,
        registration_date=None,
        fullname=None,
        linkedin=None,
        facebook=None,
        twitter=None,
        location=None,
        work=None,
    ):
        if not email:
            raise ValueError("An email address must be entered")
        if not name:
            raise ValueError("A name must be entered")

        user = self.model(
            name=name,
            email=self.normalize_email(email),
            affiliation=affiliation,
            profile_img=profile_img,
            registration_date=registration_date,
            fullname=fullname,
            linkedin=linkedin,
            facebook=facebook,
            twitter=twitter,
            location=location,
            work=work,
        )

        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        name,
        email,
        affiliation,
        profile_img,
        registration_date,
        fullname,
        linkedin,
        facebook,
        twitter,
        location,
        work,
    ):
        user = self.create_user(
            name,
            email,
            affiliation=affiliation,
            profile_img=profile_img,
            registration_date=registration_date,
            fullname=fullname,
            linkedin=linkedin,
            facebook=facebook,
            twitter=twitter,
            location=location,
            work=work,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

    def create_devuser(self, name, email):
        if not email:
            raise ValueError("An email address must be entered")
        if not name:
            raise ValueError("A name must be entered")
        user = self.model(
            name=name,
            email=self.normalize_email(email),
            affiliation=name,
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

    # TODO @jh-RLI: Check later - keep for now
    # def get_table_group_memberships(self):
    #     return GroupPermission.objects.filter(holder__in=self).prefetch_related('table') # noqa


# class ScenarioBundlePermissionGroup(Group):


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
    name = models.CharField(max_length=50, unique=True, verbose_name="Username")
    affiliation = models.CharField(max_length=50, blank=True)
    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)
    profile_img = models.ImageField(null=True, blank=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    fullname = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Full Name"
    )
    work = models.CharField(max_length=50, null=True, blank=True)
    facebook = models.URLField(max_length=500, blank=True, null=True)
    linkedin = models.URLField(max_length=500, blank=True, null=True)
    twitter = models.URLField(max_length=500, blank=True, null=True)
    location = models.CharField(max_length=50, blank=True, null=True)

    did_agree = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    ###################################################################
    is_mail_verified = models.BooleanField(default=False)  # TODO: remove
    ###################################################################

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

    def get_table_memberships(self):
        direct_memberships = self.table_permissions.all().prefetch_related("table")
        return direct_memberships

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


class ActivationToken(models.Model):
    user = models.ForeignKey(myuser, on_delete=models.CASCADE)
    value = models.TextField()


class UserPermission(TablePermission):
    holder = models.ForeignKey(
        myuser, related_name="table_permissions", on_delete=models.CASCADE
    )


class GroupPermission(TablePermission):
    holder = models.ForeignKey(
        UserGroup, related_name="table_permissions", on_delete=models.CASCADE
    )


class GroupMembership(models.Model):
    choices = (
        (NO_PERM, "None"),
        (WRITE_PERM, "Invite"),
        (DELETE_PERM, "Remove"),
        (ADMIN_PERM, "Admin"),
    )
    user = models.ForeignKey(
        myuser, related_name="memberships", on_delete=models.CASCADE
    )
    group = models.ForeignKey(
        UserGroup, related_name="memberships", on_delete=models.CASCADE
    )
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
                return myuser.objects.get(name=username)
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
