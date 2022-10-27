from django.db import models

class UserModel(models.Model):
    firstName = models.CharField(max_length=100)
    lastName = models.CharField(max_length=100)
