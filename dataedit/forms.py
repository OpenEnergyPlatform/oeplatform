from django import forms
from django.db import models
from django.forms import ModelForm

from dataedit.models import View

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


class GraphViewForm(ModelForm):
    class Meta:
        model = View
        fields = "__all__"
        exclude = ("table", "schema", "VIEW_TYPES", "options", "type")

    def __init__(self, *args, **kwargs):
        columns = kwargs.pop("columns", None)
        super(GraphViewForm, self).__init__(*args, **kwargs)

        if columns is not None:
            self.fields["column_x"] = forms.ChoiceField(choices=columns)
            self.fields["column_y"] = forms.ChoiceField(choices=columns)


class MapViewForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.columns = [c for (c, _) in kwargs.pop("columns", {})]
        super(MapViewForm, self).__init__(*args, **kwargs)

    class Meta:
        model = View
        fields = "__all__"
        exclude = ("table", "schema", "VIEW_TYPES", "options", "type")

    def save(self, commit=True):
        view = View.objects.create(
            name=self.data["name"],
            table=self.table,
            schema=self.schema,
            type="map",
            options=self.options,
            is_default=self.data.get("is_default", "off") == "on",
        )
        if commit:
            view.save()
            return view.id
        else:
            return None


class LatLonViewForm(MapViewForm):
    expected_lat_colum_names = ["lat", "latitude"]
    expected_lon_colum_names = ["lon", "longitude"]

    def __init__(self, *args, **kwargs):
        super(LatLonViewForm, self).__init__(*args, **kwargs)
        if self.columns is not None:
            self.fields["lat"] = forms.ChoiceField(
                choices=[(c, c) for c in self.columns]
            )
            for lat in self.expected_lat_colum_names:
                if lat in self.columns:
                    self.fields["lat"].initial = lat

            self.fields["lon"] = forms.ChoiceField(
                choices=[(c, c) for c in self.columns]
            )
            for lon in self.expected_lon_colum_names:
                if lon in self.columns:
                    self.fields["lon"].initial = lon

    def is_valid(self):
        return (
            super(LatLonViewForm, self).is_valid()
            and (self.options["lat"] in self.columns)
            and (self.options["lon"] in self.columns)
        )


class GeomViewForm(MapViewForm):
    expected_geom_colum_names = [
        "geom",
        "geometry",
        "point",
        "polygon",
        "line",
        "multipolygon",
    ]

    def __init__(self, *args, **kwargs):
        super(GeomViewForm, self).__init__(*args, **kwargs)
        if self.columns is not None:
            print(self.columns)
            self.fields["geom"] = forms.ChoiceField(
                choices=[(c, c) for c in self.columns]
            )

            for g in self.expected_geom_colum_names:
                if g in self.columns:
                    self.fields["geom"].initial = g

    def is_valid(self):
        return (
            super(GeomViewForm, self).is_valid()
            and self.options["geom"] in self.columns
        )
