from django import forms
from django.db import models
from django.forms import ModelForm

from dataedit.models import Tag, View

# This structure maps postgresql data types to django forms
typemap = [
    (["smallint"], models.SmallIntegerField),
    (["integer", "serial"], forms.IntegerField),
    (["bigint", "bigserial"], models.BigIntegerField),
    (["decimal", "numeric", "real", "double precision", "money"], models.DecimalField),
    (
        ["character varying(", "varying(", "varchar(", "character(", "char(", "text"],
        forms.CharField,
    ),
    (["timestamp", "date", "time"], forms.DateTimeField),
    (["bytea"], forms.CharField),
    (["interval"], models.DurationField),
    (["boolean"], models.BooleanField),
    (["point", "line", "lseg", "box", "path", "polygon", "circle"], forms.CharField),
    (["cidr", "inet", "macaddr"], forms.CharField),
    (["bit(", "bit varying("], forms.CharField),
    (["uuid"], models.UUIDField),
    (["xml"], forms.CharField),
]
# TODO:  add missing types: Textsearch, Enumeration, \
#       Composite types, Object Identifier Types, Pseudo-Types


def type2field(typename: str):
    additionals = {}
    resField = None
    typename = typename.lower()
    for (keyList, field) in typemap:
        if any(typename.startswith(key) for key in keyList):
            resField = field
    if "[" in typename:
        return resField
    if not resField:
        raise Exception(
            "type '{0}' does not \
translate to a django field".format(
                typename
            )
        )

    for _ in range(typename.count("[") - 1):
        resField = ArrayField(resField())
    if "[" in typename:
        resField = lambda **x: ArrayField(resField(), **x)

    return resField


class InputForm(forms.Form):
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", [])
        values = kwargs.pop("values", [])
        super(forms.Form, self).__init__(*args, **kwargs)
        for (name, typename) in fields:
            self.fields[name] = type2field(typename)(label=name)
            if name in values:
                self.fields[name].initial = values[name]


class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()


class UploadMapForm(forms.Form):
    """calculates the largest common subsequence of two strings"""

    def _lcs(self, s1, s2):
        m = [[0] * (1 + len(s2)) for i in range(1 + len(s1))]
        longest, x_longest = 0, 0
        for x in range(1, 1 + len(s1)):
            for y in range(1, 1 + len(s2)):
                if s1[x - 1] == s2[y - 1]:
                    m[x][y] = m[x - 1][y - 1] + 1
                    if m[x][y] > longest:
                        longest = m[x][y]
                        x_longest = x
                else:
                    m[x][y] = 0
        return longest

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields")
        headers = kwargs.pop("headers")
        super(forms.Form, self).__init__(*args, **kwargs)
        for (name, typename) in fields:
            self.fields[name] = forms.ChoiceField(
                label=name, choices=((x, x) for x in ["---"] + headers)
            )
            if any(self._lcs(name, x) / min(len(name), len(x)) > 0.7 for x in headers):
                self.fields[name].initial = max(
                    headers, key=lambda x: self._lcs(name, x)
                )
            else:
                self.fields[name].initial = "---"


class GraphViewForm(ModelForm):

    class Meta:
        model = View
        fields = '__all__'
        exclude = ('table', 'schema', 'VIEW_TYPES', 'options', 'type')

    def __init__(self, *args, **kwargs):
        columns = kwargs.pop('columns', None)
        super(GraphViewForm, self).__init__(*args, **kwargs)

        if columns is not None:
            self.fields['column_x'] = forms.ChoiceField(choices=columns)
            self.fields['column_y'] = forms.ChoiceField(choices=columns)


class MapViewForm(ModelForm):

    def __init__(self, *args, **kwargs):
        self.columns = [c for (c, _) in kwargs.pop('columns', {})]
        super(MapViewForm, self).__init__(*args, **kwargs)


    class Meta:
        model = View
        fields = '__all__'
        exclude = ('table', 'schema', 'VIEW_TYPES', 'options', 'type')

    def save(self, commit=True):
        view = View.objects.create(
            name=self.data["name"],
            table=self.table,
            schema=self.schema,
            type="map",
            options=self.options,
            is_default= self.data.get("is_default", "off") == "on"
        )
        if commit:
            view.save()
            return view.id
        else:
            return None

class LatLonViewForm(MapViewForm):
    def __init__(self, *args, **kwargs):
        super(LatLonViewForm, self).__init__(*args, **kwargs)
        if self.columns is not None:
            self.fields['lat'] = forms.ChoiceField(choices=[(c,c) for c in self.columns])
            self.fields['lon'] = forms.ChoiceField(choices=[(c,c) for c in self.columns])

    def is_valid(self):
        return super(LatLonViewForm, self).is_valid() and (self.options['lat'] in self.columns) and (self.options['lon'] in self.columns)


class GeomViewForm(MapViewForm):
    def __init__(self, *args, **kwargs):
        super(GeomViewForm, self).__init__(*args, **kwargs)
        if self.columns is not None:
            self.fields['geom'] = forms.ChoiceField(choices=[(c,c) for c in self.columns])

    def is_valid(self):
        return super(GeomViewForm, self).is_valid() and self.options['geom'] in self.columns


class TagForm(ModelForm):
    class Meta:
        model = Tag
        fields = ["label"]
