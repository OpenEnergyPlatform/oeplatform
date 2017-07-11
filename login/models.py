from django.db import models
from django.contrib import auth
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)
from django.contrib.auth.models import Group
from django.contrib.auth.models import PermissionsMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from api import actions
import requests
import json

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
import oeplatform.securitysettings as sec
import dataedit.models as datamodels

def addcontenttypes():
    """
    Insert all schemas that are present in the external database specified in
    oeplatform/securitysettings.py in the django_content_type table. This is
    important for the Group-Permission-Management.
    """
    insp = actions.connect()
    engine = actions._get_engine()
    conn = engine.connect()
    query = 'SELECT schemaname FROM pg_tables WHERE  schemaname NOT LIKE \'\_%%\' group by schemaname;'.format(st='%\_%')
    res = conn.execute(query)
    for schema in res:
        if not schema.schemaname in ['information_schema', 'pg_catalog']:
            query = 'SELECT tablename as tables FROM pg_tables WHERE schemaname = \'{s}\' AND tablename NOT LIKE \'\_%%\';'.format(s=schema.schemaname)
            table = conn.execute(query)
            for tab in table:
                _create_tableperm(schema=schema.schemaname, table=tab.tables)


def _create_tableperm(schema, table):
    """
    Create Content Type and Permissions for the given schema and table
    :param schema: Name of the schema
    :param table: Name of the table
    """
    ct_add, _ = ContentType.objects.get_or_create(app_label=schema, model=table)
    p_add = Permission.objects.get_or_create(name='Can add data in {s}.{t} '.format(s=schema, t=table),
                                             codename='add_{s}_{t}'.format(s=schema, t=table),
                                             content_type=ct_add)
    p_change = Permission.objects.get_or_create(name='Can change data in {s}.{t} '.format(s=schema, t=table),
                                                codename='change_{s}_{t}'.format(s=schema, t=table),
                                                content_type=ct_add)
    p_delete = Permission.objects.get_or_create(name='Can delete data from {s}.{t} '.format(s=schema, t=table),
                                                codename='delete_{s}_{t}'.format(s=schema, t=table),
                                                content_type=ct_add)


class UserManager(BaseUserManager):
    def create_user(self, name, mail_address, affiliation=None):
        if not mail_address:
            raise ValueError('An email address must be entered')
        if not name:
            raise ValueError('A name must be entered')

        user = self.model(name=name, mail_address=self.normalize_email(mail_address),
                          affiliation=affiliation, )

        user.save(using=self._db)
        return user

    def create_superuser(self, name, mail_address, affiliation):

        user = self.create_user(name, mail_address,
                                affiliation=affiliation)
        user.is_admin = True
        user.save(using=self._db)
        return user


class PermissionHolder:
    permissions = models.ManyToManyField(datamodels.Table,
                                         related_name='writers')


    def has_write_permissions(self, schema, table):
        """
        This function returns the authorization given the schema and table.
        """
        return self.permissions.get(name=schema, schema__name=schema).exists()

    def has_delete_permissions(self, schema, table):
        """
        This function returns the authorization given the schema and table.
        """
        return self.permissions.get(name=schema, schema__name=schema).exists()

    def has_admin_permissions(self, schema, table):
        """
        This function returns the authorization given the schema and table.
        """
        return self.permissions.get(name=schema, schema__name=schema).exists()

class UserGroup(PermissionHolder):
    pass


class Permission(models.Model):
    table = models.ForeignKey(datamodels.Table, primary_key=True)
    user = models.ForeignKey(myuser, primary_key=True, related_name='permissions')
    group = models.ForeignKey(Group, primary_key=True, related_name='permissions')
    permission = models.IntegerField(choices=((0,'None'), (1,'Write'),
                                              (2,'Delete'), (3,'Admin')))


class myuser(AbstractBaseUser, PermissionHolder):
    name = models.CharField(max_length=50, unique=True)
    affiliation = models.CharField(max_length=50, null=True)
    mail_address = models.EmailField(verbose_name='email address',
                                     max_length=255, unique=True, )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    groupadmin = models.ManyToManyField(UserGroup)

    USERNAME_FIELD = 'name'

    REQUIRED_FIELDS = [name]

    if sec.DEBUG:
        objects = UserManager()

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    def __str__(self):  # __unicode__ on Python 2
        return self.name

    @property
    def is_staff(self):
        return self.is_admin


class UserBackend(object):
    def authenticate(self, username=None, password=None):
        url = 'https://wiki.openmod-initiative.org/api.php?action=login'
        data = {'format':'json', 'lgname':username}

        #A first request to receive the required token
        token_req = requests.post(url, data)
        data['lgpassword'] = password
        data['lgtoken'] = token_req.json()['login']['token']

        # A second request for the actual authentication
        login_req = requests.post(url, data, cookies=token_req.cookies)

        if login_req.json()['login']['result'] == 'Success':
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