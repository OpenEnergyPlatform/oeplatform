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
    label = CharField(max_length=50, null=False, unique=True)
    color = ColorField(default='#FF0000')
    def get_absolute_url(self):
        return reverse('tag', kwargs={'pk': self.pk})
    def __str__(self):
        return "%s (%s)"%(self.label, self.id)


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

