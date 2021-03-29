from django.forms.widgets import TextInput, Widget, MultiWidget
from django_better_admin_arrayfield.forms.widgets import DynamicArrayWidget
from django import forms


class FactoryWidget(MultiWidget):
    template_name = "modelview/widgets/multiwidget.html"

    def __init__(self, factory):
        self.factory = factory
        self.widget_dict = {
            fn: f._widget for fn, f in factory._fields.items()
        }
        self.verbose_names = {('_%s' % fn): f.verbose_name for fn, f in factory._fields.items() if f.verbose_name}
        super().__init__(widgets=self.widget_dict)

    def decompress(self, value):
        return [f for f in value.iter_fields()]

    def get_structure(self):
        return self.factory.build_structure_spec()

    def build_template_structure(self, prefix):
        d = self.factory.build_template_structure(prefix)
        fac = self.factory()
        d[prefix] = self.render("", fac, attrs={"id": "{prefix}"})
        return d

    def get_context(self, name, value, attrs):
        context = super(MultiWidget, self).get_context(name, value, attrs)
        if self.is_localized:
            for widget in self.widgets:
                widget.is_localized = self.is_localized
        # value is a list of values, each corresponding to a widget
        # in self.widgets.
        if not isinstance(value, list):
            value = self.decompress(value)

        final_attrs = context['widget']['attrs']
        input_type = final_attrs.pop('type', None)
        id_ = final_attrs.get('id')

        subwidgets = []
        for i, (widget_name, widget) in enumerate(zip(self.widgets_names, self.widgets)):
            vname = self.verbose_names.get(widget_name)
            if input_type is not None:
                widget.input_type = input_type
            widget_name = name + widget_name
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None
            if id_:
                widget_attrs = final_attrs.copy()
                widget_attrs['id'] = '%s.%s' % (id_, widget_value.field_name)
            else:
                widget_attrs = final_attrs
            if vname:
                widget_attrs['verbose_name'] = vname
            subcontext = widget.get_context(widget_name, widget_value, widget_attrs)['widget']
            subwidgets.append(subcontext)
        context['widget']['subwidgets'] = subwidgets

        return context


def _factory_field(factory):
    def inner():
        return FactoryWidget(factory)

    return inner


class DynamicFactoryArrayWidget(forms.TextInput):
    template_name = "modelview/widgets/dynamic_array.html"

    def __init__(self, *args, **kwargs):
        self.subwidget_form = kwargs.pop("subwidget_form", forms.TextInput)
        self.subwidget_kwargs_gen = kwargs.pop("subwidget_form_kwargs_gen", None)
        if self.subwidget_kwargs_gen is None:
            self.subwidget_kwargs_gen = lambda: dict()
        super().__init__(*args, **kwargs)

    @property
    def is_hidden(self):
        return self.subwidget_form(**self.subwidget_kwargs_gen()).is_hidden

    def get_context(self, name, value, attrs):
        if value and value.values:
            context_value = value.values
        else:
            context_value = []
        attrs["class"] = attrs.get("class", "" ) + " form-control"
        context = super().get_context(name, context_value, attrs)
        final_attrs = context["widget"]["attrs"]
        id_ = context["widget"]["attrs"].get("id")
        context["widget"]["is_none"] = value is None

        subwidgets = []
        for index, item in enumerate(context["widget"]["value"]):
            widget_attrs = final_attrs.copy()
            if id_ is not None:
                widget_attrs["id"] = "{id_}.{index}".format(id_=id_, index=index)
            widget = self.subwidget_form(**self.subwidget_kwargs_gen())
            widget.is_required = self.is_required
            subwidgets.append(widget.get_context(name, item, widget_attrs)["widget"])

        context["widget"]["subwidgets"] = subwidgets
        empty_widget = self.subwidget_form(**self.subwidget_kwargs_gen())
        if isinstance(empty_widget, FactoryWidget):
            context["widget"]["attrs"]["identifier"] = empty_widget.factory._factory_id
        return context

    def get_structure(self):
        if isinstance(self.subwidget_form, type) and issubclass(
            self.subwidget_form, Widget
        ):
            return self.subwidget_form(**self.subwidget_kwargs_gen()).render("", None)
        else:
            return None

    def build_template_structure(self, prefix):

        if isinstance(self.subwidget_form, type) and issubclass(
            self.subwidget_form, Widget
        ):
            d = {prefix: self.subwidget_form(**self.subwidget_kwargs_gen()).render("", None, attrs={"id": "{prefix}", "class": "form-control"})}
        else:
            d = self.subwidget_form(**self.subwidget_kwargs_gen()).build_template_structure(prefix)
        return d


    def value_from_datadict(self, data, files, name):
        try:
            getter = data.getlist
            return [value for value in getter(name) if value]
        except AttributeError:
            return data.get(name)

    def value_omitted_from_data(self, data, files, name):
        return False

    def format_value(self, value):
        return value or []
