from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)
from django.contrib.auth.models import User
import mwclient as mw

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

class myuser(AbstractBaseUser):
    name = models.CharField(max_length=50, unique=True)
    affiliation = models.CharField(max_length=50)
    mail_address = models.EmailField(verbose_name='email address',
                                     max_length=255, unique=True, )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'name'

    REQUIRED_FIELDS = [name]

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

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

