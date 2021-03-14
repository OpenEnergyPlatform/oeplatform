from django.forms.widgets import TextInput, HiddenInput, Select
from django.utils.html import format_html, format_html_join, mark_safe
import rdflib as rl

from modelview.rdf import handler, widget, factory, connection

from modelview.rdf.widget import DynamicFactoryArrayWidget

class Field:
    """
    :ivar rdf_name: IRI of this property
    :ivar verbose_name: A readable label (not `rdfs:label`)
    :ivar handler: A handler used to parse this field. Defaults to `handler.DefaultHandler`
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
        widget_kwargs_gen=None,
        inverse=False
    ):
        self.rdf_name = rdf_name  # Some IRI
        self.verbose_name = verbose_name
        self.handler = handler if handler else self._handler()
        self.help_text = help_text
        self._widget = DynamicFactoryArrayWidget(subwidget_form=widget_cls, subwidget_form_kwargs_gen=widget_kwargs_gen)
        self.inverse = inverse

    def widget(self):
        return self._widget

    def fetch_query(self, subject, object, filter=None, options=None):
        if filter is None:
            filter = []
        filter = filter.copy()
        filter.append(f"?p = <{self.rdf_name}>")
        if options is None:
            options = []
        if self.inverse:
            query = f"{object} ?p {subject}."
        else:
            query = f"{subject} ?p {object}."
        for o in options:
            query += f"OPTIONAL {{ {o} }} . "
        if filter:
            query += f"FILTER ({' && ' .join(filter)}) . "
        return query


class IRIField(Field):

    def __init__(self, rdf_name, **kwargs):
        super().__init__(rdf_name, widget_cls=HiddenInput, handler=handler.IRIHandler(), **kwargs)


class PredefinedInstanceField(Field):
    _handler = handler.IRIHandler

    def __init__(self, rdf_name, filter, subclass=False, **kwargs):
        self.filter = filter
        self.subclass = subclass
        super().__init__(rdf_name, widget_cls=Select, handler=handler.IRIHandler(), widget_kwargs_gen=self._get_kwargs, **kwargs)

    def _get_kwargs(self):
        return dict(choices=self._load_choices(), attrs=dict(autocomplete="off"))

    def _load_choices(self):
        c = connection.ConnectionContext()
        results = c.load_all(self.filter, self.subclass, inverse=self.inverse)
        choices = [(row.get("label", row['iri'])['value'], row['iri']['value']) for row in results["results"]["bindings"]]
        return choices


class FactoryField(Field):
    def __init__(self, factory, **kwargs):
        super(FactoryField, self).__init__(**kwargs)
        self.factory = factory
        self._widget = DynamicFactoryArrayWidget(
            subwidget_form=widget._factory_field(factory)
        )

    def structure(self):
        return self._widget.get_structure()


class Container(handler.Rederable):
    def __init__(self, field):
        self.field = field
        self.values = []

    def to_triples(self, subject):
        if self.field.rdf_name and self.values is not None:
            for v in self.values:
                if isinstance(v, (rl.Literal, rl.URIRef)):
                    yield subject, self.field.rdf_name, v
                elif isinstance(v, factory.RDFFactory):
                    yield subject, self.field.rdf_name, v.iri.values[0]
                    for t in v.to_triples():
                        yield t
                else:
                    raise Exception(v)

    def render(self, mode="display", **kwargs):
        it = list(self.values if self.values else ["-"])

        if mode == "display":
            f = self._render_atomic_field

            vals = [(f(v),) for v in it]

            s = format_html(
                mark_safe(
                    '<tr><th><a href="{rdfname}">{vname}</a></th><td>{vals}</td></tr>'
                ),
                rdfname=self.field.rdf_name,
                vname=self.field.verbose_name,
                vals=format_html_join(" ", '<li class="list-group-item">{}</li>', vals),
            )
            return s
        else:
            return self.field._widget.render("Name", self, {"id": "field", "level": 0})

    def to_form_element(self):
        return self.field._widget.render(self.field_name, self, attrs={"id": self.field_name})

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