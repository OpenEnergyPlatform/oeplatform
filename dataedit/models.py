from datetime import datetime

from colorfield.fields import ColorField
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKey,
    IntegerField,
)
from django.utils import timezone

# Create your models here.


class TableRevision(models.Model):
    table = CharField(max_length=1000, null=False)
    schema = CharField(max_length=1000, null=False)
    date = DateTimeField(max_length=1000, null=False, default=datetime.now)
    created = DateTimeField(null=False, default=timezone.now)
    path = CharField(max_length=1000, null=False)
    size = IntegerField(null=False)
    last_accessed = DateTimeField(null=False, default=timezone.now)


class Tag(models.Model):
    label = CharField(max_length=50, null=False, unique=True)
    color = ColorField(default="#FF0000")

    #def get_absolute_url(self):
    #    return reverse("tag", kwargs={"pk": self.pk})


class Tagable(models.Model):
    name = CharField(max_length=1000, null=False)
    tags = models.ManyToManyField(Tag)

    class Meta:
        abstract = True


class Schema(Tagable):
    class Meta:
        unique_together = (("name"),)


class Table(Tagable):
    schema = models.ForeignKey(Schema, on_delete=models.CASCADE)

    @classmethod
    def load(cls, schema, table):
        table_obj, _ = Table.objects.get_or_create(
            name=table, schema=Schema.objects.get_or_create(name=schema)[0]
        )

        return table_obj

    class Meta:
        unique_together = (("schema", "name"),)


class View(models.Model):
    name = CharField(max_length=50, null=False)
    table = CharField(max_length=1000, null=False)
    schema = CharField(max_length=1000, null=False)
    VIEW_TYPES = (("table", "table"), ("map", "map"), ("graph", "graph"))
    type = CharField(max_length=10, null=False, choices=VIEW_TYPES)
    options = JSONField(null=False, default=dict)
    is_default = BooleanField(default=False)

    def __str__(self):
        return '{}/{}--"{}"({})'.format(self.schema, self.table, self.name, self.type.upper())


class Filter(models.Model):
    column = CharField(max_length=100, null=False)
    FILTER_TYPES = (("equal", "equal"), ("range", "range"))
    type = CharField(max_length=10, null=False, choices=FILTER_TYPES)
    value = JSONField(null=False)
    view = ForeignKey(View, on_delete=models.CASCADE, related_name="filter")
