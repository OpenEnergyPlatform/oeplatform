from django.forms.widgets import TextInput, Widget, MultiWidget
from django_better_admin_arrayfield.forms.widgets import DynamicArrayWidget


class FactoryWidget(MultiWidget):
    def __init__(self, factory):
        self.factory = factory
        self.widget_dict = {
            f: getattr(factory, f)._widget for f in factory.iter_field_names()
        }
        super().__init__(widgets=self.widget_dict)

    def decompress(self, value):
        return [f for f in value.iter_fields()]

    def get_structure(self):
        return self.factory.build_structure_spec()


def _factory_field(factory):
    def inner():
        return FactoryWidget(factory)

    return inner


class DynamicFactoryArrayWidget(DynamicArrayWidget):
    def get_context(self, name, value, attrs):
        context_value = value.values or [""]
        return super().get_context(name, context_value, attrs)

    def get_structure(self):
        if isinstance(self.subwidget_form, type) and issubclass(
            self.subwidget_form, Widget
        ):
            return self.subwidget_form().render("", None)
        else:
            return self.subwidget_form().get_structure()
