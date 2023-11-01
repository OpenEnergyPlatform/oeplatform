from django.db import models
from django.utils import timezone


class OEKG_Modifications(models.Model):
    old_state = models.JSONField()
    new_state = models.JSONField()
    user = models.CharField(max_length=200)
    timestamp = models.DateTimeField(default=timezone.now)
