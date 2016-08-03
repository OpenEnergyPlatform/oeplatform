from django.db import models
from django.db.models import CharField, DateTimeField
from django.utils import timezone
from django.core.urlresolvers import reverse
from colorfield.fields import ColorField

# Create your models here.

class TableRevision(models.Model):
    table = CharField(max_length=1000, null=False)
    schema = CharField(max_length=1000, null=False)
    revision = CharField(max_length=1000, null=False)
    created = DateTimeField(null=False, default=timezone.now)
    last_accessed = DateTimeField(null=False, default=timezone.now)


class Tag(models.Model):
    label = CharField(max_length=50, null=False)
    color = ColorField(default='#FF0000')
    def get_absolute_url(self):
        return reverse('tag', kwargs={'tag_id': self.pk})


class Tagable(models.Model):
    name = CharField(max_length=1000, null=False)
    tags = models.ManyToManyField(Tag)
    class Meta:
        abstract = True

class Schema(Tagable):
    pass

class Table(Tagable):
    schema = models.ForeignKey(Schema)

