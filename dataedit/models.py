from django.db import models
from django.db.models import CharField, DateTimeField, BooleanField
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
    label = CharField(max_length=50, null=False, unique=True)
    color = ColorField(default='#FF0000')


    def get_absolute_url(self):
        return reverse('tag', kwargs={'pk': self.pk})



class Tagable(models.Model):
    name = CharField(max_length=1000, null=False)
    tags = models.ManyToManyField(Tag)
    class Meta:
        abstract = True

class Schema(Tagable):
    class Meta:
        unique_together = (("name"),)

class Table(Tagable):
    schema = models.ForeignKey(Schema)

    class Meta:
        unique_together = (("schema", "name"),)


class View(models.Model):
    name = CharField(max_length=50, null=False)
    table = CharField(max_length=1000, null=False)
    schema = CharField(max_length=1000, null=False)
    type = CharField(max_length=10, null=False)
    data = CharField(max_length=3000, null=False)
    is_default = BooleanField(default=False)