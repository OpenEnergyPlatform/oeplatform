from datetime import datetime

from colorfield.fields import ColorField
# django.contrib.postgres.fields.JSONField is deprecated.
from django.db.models import JSONField
from django.db import models
from django.db.models import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKey,
    IntegerField,
)
from django.utils import timezone
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django import forms
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation

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
    search = SearchVectorField(default="")
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


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE)
    content = models.TextField()
    comment_time = models.DateTimeField(default = timezone.now)
    schema_name = models.TextField()
    table_name = models.TextField()

    liked_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name = "liked_user")
    disked_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name = "disliked_user")
    parent = models.ForeignKey('self', blank=True, null=True, on_delete = models.CASCADE, related_name = "+")

    def children(self):
        return Comment.objects.filter(parent=self)

    @property
    def is_parent(self):
        if self.parent is not None:
            return False
        else:
            return True
	
    class Meta:
        db_table = 'comment'
        ordering = ['-comment_time']


class CommentForm(forms.ModelForm):
    content = forms.CharField(label ="", widget = forms.Textarea(
    attrs ={
        'class':'form-control',
        'placeholder':'write a comment !',
        'rows':5,
        'cols':-5,
	    'id' : 'summernote',
    }))
    class Meta:
        model = Comment
        fields =['content']
