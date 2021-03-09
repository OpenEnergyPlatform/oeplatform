from django.forms.widgets import TextInput
from django.utils.html import format_html, format_html_join, mark_safe
import json

from modelview.rdf import handler, widget

from modelview.rdf.widget import DynamicFactoryArrayWidget


class Field(handler.Rederable):
    """
    :ivar rdf_name: IRI of this property
    :ivar verbose_name: A readable label (not `rdfs:label`)
    :ivar handler: A handler used to parse this field. Defaults to `handler.DefaultHandler`
    :ivar values: A list of values that the related subject is in relation with
    :ivar help_text: Some helpful text
    """

    _handler = handler.DefaultHandler

    def __init__(
        self,
        rdf_name,
        verbose_name=None,
        handler: handler.Handler = None,
        help_text: str = None,
        widget_cls=TextInput,
    ):
        self.rdf_name = rdf_name  # Some IRI
        self.verbose_name = verbose_name
        self.handler = handler if handler else self._handler()
        self.values = None
        self.help_text = help_text
        self._widget = DynamicFactoryArrayWidget(subwidget_form=widget_cls)

    def to_triples(self, subject):
        if self.values is not None:
            for v in self.values:
                yield f"{subject} {self.rdf_name} {v} ."

    def render(self, mode="display", **kwargs):
        it = list(self.values if self.values else ["-"])

        if mode == "display":
            f = self._render_atomic_field

            vals = [(f(v),) for v in it]

            s = format_html(
                mark_safe(
                    '<tr><th><a href="{rdfname}">{vname}</a></th><td>{vals}</td></tr>'
                ),
                rdfname=self.rdf_name,
                vname=self.verbose_name,
                vals=format_html_join(" ", '<li class="list-group-item">{}</li>', vals),
            )
            return s
        else:
            return self._widget.render("Name", self, {"id": "field", "level": 0})

    def render_fields(self):
        return self.render(mode="form")

    def structure(self):
        return self._widget()

    def _render_atomic_field(self, obj, **kwargs):
        if isinstance(obj, handler.Rederable):
            return obj.render()
        elif isinstance(obj, list):
            return [self._render_atomic_field(o, **kwargs) for o in obj]
        elif isinstance(obj, str):
            return obj
        elif obj is None:
            return None
        else:
            raise ValueError(obj)


class FactoryField(Field):
    def __init__(self, factory, **kwargs):
        super(FactoryField, self).__init__(**kwargs)
        self.factory = factory
        self._widget = DynamicFactoryArrayWidget(
            subwidget_form=widget._factory_field(factory)
        )

    def structure(self):
        return self._widget.get_structure()
