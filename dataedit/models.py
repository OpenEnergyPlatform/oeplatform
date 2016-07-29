from django.db import models
from django.db.models import CharField, DateTimeField
from django.utils import timezone
# Create your models here.

class TableRevision(models.Model):
    table = CharField(max_length=1000, null=False)
    schema = CharField(max_length=1000, null=False)
    revision = CharField(max_length=1000, null=False)
    created = DateTimeField(null=False, default=timezone.now)
    last_accessed = DateTimeField(null=False, default=timezone.now)
