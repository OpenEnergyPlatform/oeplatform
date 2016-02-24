from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)

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
	name=models.CharField(max_length=50)
	affiliation=models.CharField(max_length=50)
	mail_address=models.EmailField(verbose_name='email address', max_length=255, unique=True,)
	is_active=models.BooleanField(default=True)
	is_admin=models.BooleanField(default=False)
	is_staff=models.BooleanField(default=False)
	objects=usermanager()


	REQUIRED_FIELDS = [name, mail_address]

