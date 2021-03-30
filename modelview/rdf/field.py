from django.forms.widgets import TextInput, HiddenInput, Select
from django.utils.html import format_html, format_html_join, mark_safe
import rdflib as rl

from modelview.rdf import handler, widget, factory, connection

from modelview.rdf.widget import DynamicFactoryArrayWidget
from os import path
from django import template
from django.template import loader


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
        filter=None,
        subclass=False,
        follow=True,
        hidden=False,
        inverse=False,
        template=None,
    ):
        self.rdf_name = rdf_name  # Some IRI
        self.verbose_name = verbose_name
        self.handler = handler if handler else self._handler()
        self.help_text = help_text
        self.filter = filter
        self.subclass = subclass
        self.follow = follow
        self.hidden = hidden
        self._widget = DynamicFactoryArrayWidget(
            subwidget_form=widget_cls, subwidget_form_kwargs_gen=widget_kwargs_gen
        )
        self.inverse = inverse
        self._template = template or {"type": "text"}
        self.is_literal = True

    def widget(self):
        return self._widget

    def _build_query_parts(
        self, subject, object, where=None, filter=None, options=None
    ):
        if filter is None:
            filter = []
        if where is None:
            where = []
        filter = filter.copy()
        filter.append(f"?p = <{self.rdf_name}>")
        if self.filter:
            where += [f"{object} {f} ." for f in self.filter]
        if options is None:
            options = []
        if self.inverse:
            where.append(f"{object} ?p {subject}.")
        else:
            where.append(f"{subject} ?p {object}.")
        return where, options, filter

    def fetch_queries(self, subject, object, where=None, filter=None, options=None):
        where, options, filter = self._build_query_parts(
            subject, object, where=where, filter=filter, options=options
        )
        query = " ".join(where)
        for o in options:
            query += f"OPTIONAL {{ {o} }} . "
        if filter:
            query += f"FILTER ({' && ' .join(filter)}) . "
        return query

    def combine_with_form(self, value, index=None):
        FORM_TEMPLATE = loader.get_template(
            path.join("modelview", "widgets", "dynamic_edit.html")
        )
        field = self._widget.subwidget_form(
            **self._widget.subwidget_kwargs_gen()
        ).render(
            "",
            value,
            {
                "class": "form-control",
                "id": "input__" + index,
                "onfocusout": f"hide_field('{index}')",
            },
        )
        return FORM_TEMPLATE.render(dict(value=value, id=index, field=field))

    @property
    def spec(self):
        return dict(
            verbose_name=self.verbose_name,
            help_text=self.help_text,
            template=self._template,
            literal=self.is_literal,
        )


class IRIField(Field):
    def __init__(self, rdf_name, **kwargs):
        super().__init__(
            rdf_name, widget_cls=HiddenInput, handler=handler.IRIHandler(), **kwargs
        )


class PredefinedInstanceField(Field):
    _handler = handler.IRIHandler

    def __init__(self, rdf_name, **kwargs):
        super().__init__(rdf_name, handler=handler.IRIHandler(), **kwargs)
        self.is_literal = False


class FactoryField(Field):
    def __init__(self, factory, **kwargs):
        if kwargs.get("handler", None) is None:
            kwargs["handler"] = handler.FactoryHandler(factory)
        super(FactoryField, self).__init__(**kwargs)
        self.factory = factory
        self._widget = DynamicFactoryArrayWidget(
            subwidget_form=widget._factory_field(factory)
        )
        self._template = None
        self.is_literal = False

    @property
    def spec(self):
        return dict(factory=self.factory._factory_id, **super(FactoryField, self).spec)


class Container(handler.Rederable):
    def __init__(self, field):
        self.field = field
        self.values = []

    def to_json(self):
        for v in self.values:
            if isinstance(v, (rl.Literal, rl.URIRef, rl.BNode)):
                yield v
            elif isinstance(v, factory.RDFFactory):
                yield v.iri.values[0]
            elif isinstance(v, handler.NamedIRI):
                return v.iri
            else:
                raise Exception(v)
