"""
SPDX-FileCopyrightText: 2025 AemanMalik <https://github.com/AemanMalik> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Marco Finkendei <https://github.com/MFinkendei>
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Lara Christmann <https://github.com/solar-c> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Lara Christmann <https://github.com/solar-c> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import itertools
from typing import TYPE_CHECKING

import requests
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, Group, UserManager
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import QuerySet
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

import dataedit.models as datamodels
from login.permissions import ADMIN_PERM, DELETE_PERM, NO_PERM, WRITE_PERM

if TYPE_CHECKING:
    # only import for static typechecking
    # TODO: is there a betetr way of doing this?
    from factsheet.models import ScenarioBundleAccessControl


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
    table_permissions: QuerySet[
        "TablePermission"
    ]  # related_name, for static type checking

    def has_write_permissions(self, table: str):
        """
        This function returns the authorization given the table.
        """
        return self.__get_perm(table=table) >= WRITE_PERM

    def has_delete_permissions(self, table: str):
        """
        This function returns the authorization given the table.
        """
        return self.__get_perm(table=table) >= DELETE_PERM

    def has_admin_permissions(self, table: str):
        """
        This function returns the authorization given the table.
        """
        return self.__get_perm(table=table) >= ADMIN_PERM

    def __get_perm(self, table: str):
        perm = self.table_permissions.filter(table__name=table).first()
        if perm:
            return perm.level
        else:
            return NO_PERM


class UserGroup(Group, PermissionHolder):
    description = models.TextField(null=False, default="")
    is_admin = models.BooleanField(null=False, default=False)

    memberships: QuerySet["GroupMembership"]  # related_name, for static type checking
    table_permissions: QuerySet[
        "GroupPermission"
    ]  # related_name, for static type checking

    def get_table_permission_level(self, table: datamodels.Table) -> int:
        if self.is_admin:
            return ADMIN_PERM
        return max(
            itertools.chain(
                [NO_PERM],
                (perm.level for perm in self.table_permissions.filter(table=table)),
            )
        )

    # TODO @Jonas Huber: Check later - keep for now
    # def get_table_group_memberships(self):
    #     return GroupPermission.objects.filter(holder__in=self).prefetch_related('table') # noqa


class TablePermission(models.Model):
    choices = (
        (NO_PERM, "None"),
        (WRITE_PERM, "Write"),
        (DELETE_PERM, "Delete"),
        (ADMIN_PERM, "Admin"),
    )
    table = models.ForeignKey(
        datamodels.Table,
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
        # NOTE: we cannot use a simple related name, because we have multiple
        # subclasses, so the reference is not deterministic.
        # With this pattern, reverse lookup is autogenerated for all subclasses
        # as '<subclass>_set' (all lower case)
    )

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

    reviewed_by: QuerySet[
        "datamodels.PeerReview"
    ]  # related_name, for static type checking
    review_received: QuerySet[
        "datamodels.PeerReview"
    ]  # related_name, for static type checking
    scenario_bundle_creator: QuerySet[
        "ScenarioBundleAccessControl"
    ]  # related_name, for static type checking
    memberships: QuerySet["GroupMembership"]  # related_name, for static type checking
    table_permissions: QuerySet[
        "UserPermission"
    ]  # related_name, for static type checking

    USERNAME_FIELD = "name"
    REQUIRED_FIELDS = [name]  # type:ignore TODO: why do we need this?

    objects = OEPUserManager()

    def get_full_name(self) -> str:
        return self.name

    def get_short_name(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name

    @property
    def is_staff(self) -> bool:
        return self.is_admin

    def get_table_memberships(self) -> QuerySet["UserPermission"]:
        direct_memberships = self.table_permissions.all().prefetch_related("table")
        return direct_memberships

    def get_groups_queryset(self) -> QuerySet["UserGroup"]:
        return UserGroup.objects.filter(memberships__user=self)

    def get_tables_queryset(
        self, min_permission_level: int = NO_PERM
    ) -> QuerySet[datamodels.Table]:
        """Return QuerySet of tables that user has some permission
        combine filter (OR) of table with direct permissions
        and with group permissions
        """
        groups = self.get_groups_queryset()

        return (
            datamodels.Table.objects.filter(
                # tables where user has direct UserPermission
                userpermission_set__holder=self,
                userpermission_set__level__gte=min_permission_level,
            )
            | datamodels.Table.objects.filter(
                # tables where user isin a group that has GroupPermission
                grouppermission_set__holder__in=groups,
                grouppermission_set__level__gte=min_permission_level,
            )
        ).distinct()

    def get_table_permission_level(self, table) -> int:
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
        except ObjectDoesNotExist:
            return None

        if user.is_native:
            if not password:
                return None

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
