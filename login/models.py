from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)
from django.contrib.auth.models import User
import requests
import json

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
import oeplatform.securitysettings as sec


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

class myuser(AbstractBaseUser):
    name = models.CharField(max_length=50, unique=True)
    affiliation = models.CharField(max_length=50, null=True)
    mail_address = models.EmailField(verbose_name='email address',
                                     max_length=255, unique=True, )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'name'

    REQUIRED_FIELDS = [name]

    if sec.DEBUG:
        objects = UserManager()

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
        url = 'https://wiki.openmod-initiative.org/api.php?action=login'
        data = {'format':'json', 'lgname':username}
        token_req = requests.post(url, data)
        data['lgpassword'] = password
        data['lgtoken'] = token_req.json()['login']['token']
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

