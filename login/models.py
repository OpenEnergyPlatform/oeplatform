from django.db import models
from django.contrib import auth
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import PermissionDenied
import mwclient as mw
from api import actions

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
import oeplatform.securitysettings as sec
from django.contrib.contenttypes.models import ContentType

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
    for shema in res:
        if not shema.schemaname in ['information_schema', 'pg_catalog']:
            query = 'SELECT tablename as tables FROM pg_tables WHERE schemaname = \'{s}\' AND tablename NOT LIKE \'\_%%\';'.format(s=shema.schemaname)
            table = conn.execute(query)
            for tab in table:             
                ContentType.objects.get_or_create(app_label=shema.schemaname, model=tab.tables)
                ct_add = ContentType.objects.get(app_label=shema.schemaname, model=tab.tables)
                p_add = Permission.objects.get_or_create(name='Can add data in {s}.{t} '.format(s=shema.schemaname, t=tab.tables),
                                   codename='add_{s}_{t}'.format(s=shema.schemaname, t=tab.tables),
                                   content_type=ct_add)
                p_change = Permission.objects.get_or_create(name='Can change data in {s}.{t} '.format(s=shema.schemaname, t=tab.tables),
                                   codename='change_{s}_{t}'.format(s=shema.schemaname, t=tab.tables),
                                   content_type=ct_add)
                p_delete = Permission.objects.get_or_create(name='Can delete data from {s}.{t} '.format(s=shema.schemaname, t=tab.tables),
                                   codename='delete_{s}_{t}'.format(s=shema.schemaname, t=tab.tables),
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

class myuser(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=50, unique=True)
    affiliation = models.CharField(max_length=50, null=True)
    mail_address = models.EmailField(verbose_name='email address',
                                     max_length=255, unique=True, )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    groupadmin = models.ManyToManyField(Group)
    
    USERNAME_FIELD = 'name'

    REQUIRED_FIELDS = [name]

    if sec.DEBUG:
        objects = UserManager()

    def has_perm(self, perm, obj=None):
        """
        
        """
        if self.is_admin:
            return True
        for backend in auth.get_backends():
            if not hasattr(backend, 'has_perm'):
                continue
            try:
                if backend.has_perm(self, perm, obj):
                    return True
            except PermissionDenied:
                return False
        return False

    def has_module_perms(self, app_label):
        """
        
        """
        if self.is_admin:
            return True
        for backend in auth.get_backends():
            if not hasattr(backend, 'has_module_perms'):
                continue
            try:
                if backend.has_module_perms(self, app_label):
                    return True
            except PermissionDenied:
                return False
        return False
    
    def get_writeable_tables(self):
        """
        
        """
        permissions = set()
        for backend in auth.get_backends():
            if hasattr(backend, "get_group_permissions"):
                permissions.update(backend.get_group_permissions(self, obj=None))
        return permissions 
    
    def get_all_avail_perms(self):
        """
        
        """
        insp = actions.connect()
        engine = actions._get_engine()
        conn = engine.connect()
        query = 'SELECT schemaname, tablename as tables FROM pg_tables WHERE pg_has_role(\'{user}\', tableowner, \'MEMBER\')AND tablename NOT LIKE \'%%\\_%%\';'.format(user=sec.dbuser)
        res = conn.execute(query)
        ct_ids = list()
        i=0
        for shema in res:
            ct_add = ContentType.objects.get(app_label=shema.schemaname, model=shema.tables)
            #ct_ids=ct_ids+'{id},'.format(id=ct_add.id)
            ct_ids.insert(i, ct_add.id)
            i+1
        print(ct_ids)
        result = Permission.objects.filter(content_type_id__in=ct_ids)
        return result
        
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
        site = mw.Site(("http","wiki.openmod-initiative.org"),"/")
        print("Login using wiki interface")
        try:
            site.login(username, password)
        except mw.errors.LoginError:
            return None
        else:
            return myuser.objects.get_or_create(name=username)[0]

    def get_user(self, user_id):
        try:
            return myuser.objects.get(pk=user_id)
        except myuser.DoesNotExist:
            return None

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

