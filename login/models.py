from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)
from django.contrib.auth.models import User

#class Person(models.Model):

#	name=models.CharField(max_length=30)
#	mail_address=models.CharField(max_length=30)
#	affiliation=models.CharField(max_length=30)

class usermanager(BaseUserManager):
	
	def create_user(self, name, mail_address, affiliation):
		if not email:
			raise ValueError('An email address must be entered')
		if not name:
			raise ValueError('A name must be entered')

		user=self.model(self.normalize_email(mail_address), name=name, affiliation=affiliation,)

		user.save(using=self._db)
		return user
		

	def create_superuser(self, name, mail_address, affiliation):

		user=self.create_user(mail_address, name=name, affiliation=affiliation)
		user.is_admin=True
		user.save(using=self._db)
		return user


class myuser(AbstractBaseUser):
	name=models.CharField(max_length=50, unique=True)
	affiliation=models.CharField(max_length=50)
	mail_address=models.EmailField(verbose_name='email address', max_length=255, unique=True,)
	is_active=models.BooleanField(default=True)
	is_admin=models.BooleanField(default=False)
	
	objects=usermanager()
	
	USERNAME_FIELD='name'

	REQUIRED_FIELDS = [name, mail_address]
	
	def get_full_name(self):
		return self.name

	def get_short_name(self):
		return self.name

	def __str__(self):			  # __unicode__ on Python 2
		return self.name
	
	def has_perm(self, perm, obj=None):
		"Does the user have a specific permission?"
		# Simplest possible answer: Yes, always
		return True

	def has_module_perms(self, app_label):
		"Does the user have permissions to view the app `app_label`?"
		# Simplest possible answer: Yes, always
		return True
	
	@property
	def is_staff(self):
		return self.is_admin

