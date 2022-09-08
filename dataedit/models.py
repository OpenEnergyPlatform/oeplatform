from django.contrib.postgres.search import SearchVectorField
from django.db import models

# django.contrib.postgres.fields.JSONField is deprecated.
from django.db.models import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKey,
    IntegerField,
    JSONField,
)
from django.utils import timezone

# Create your models here.


class TableRevision(models.Model):
    table = CharField(max_length=1000, null=False)
    schema = CharField(max_length=1000, null=False)
    date = DateTimeField(max_length=1000, null=False, default=timezone.now)
    created = DateTimeField(null=False, default=timezone.now)
    path = CharField(max_length=1000, null=False)
    size = IntegerField(null=False)
    last_accessed = DateTimeField(null=False, default=timezone.now)


class Tagable(models.Model):
    name = CharField(max_length=1000, null=False)

    class Meta:
        abstract = True


class Schema(Tagable):
    class Meta:
        unique_together = (("name"),)


class Table(Tagable):
    schema = models.ForeignKey(Schema, on_delete=models.CASCADE)
    search = SearchVectorField(default="")
    # Add field to store oemetadata related to the table and avoide performance issues
    # due to oem string (json) parsing like when reading the oem form comment on table
    oemetadata = JSONField(null=True)

    @classmethod
    def load(cls, schema, table):
        table_obj = Table.objects.get(
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
        return '{}/{}--"{}"({})'.format(
            self.schema, self.table, self.name, self.type.upper()
        )


class Filter(models.Model):
    column = CharField(max_length=100, null=False)
    FILTER_TYPES = (("equal", "equal"), ("range", "range"))
    type = CharField(max_length=10, null=False, choices=FILTER_TYPES)
    value = JSONField(null=False)
    view = ForeignKey(View, on_delete=models.CASCADE, related_name="filter")


# class OEMetadataStorage(models.Model):
#     '''
#     Store oemetadata if present on table. As this was stored as SQL comment on 
#     table before we will keep the comment but from now on also store it in this 
#     table as soon as it is added to the table (as SQL comment on table). This 
#     ensures not to breake the legacy functionality.
#     '''

#     schema = CharField(max_length=100, null=False)
#     table = CharField(max_length=100, null=False)
#     oem = JSONField(null=False)
