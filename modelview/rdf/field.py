from abc import ABC
from os import path

import rdflib as rl
from django.forms.widgets import TextInput
from django.template import loader

from api.error import APIError
from modelview.rdf import factory, handler, widget
from modelview.rdf.widget import DynamicFactoryArrayWidget


class Field(ABC):
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
        self.is_literal = True

    @property
    def template(self):
        raise NotImplementedError

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

    @property
    def _label_option(self):
        return "?o rdfs:label ?lo"

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
            template=self.template,
            literal=self.is_literal,
        )

    def process_data(self, data):
        raise NotImplementedError


class TextField(Field):
    @property
    def template(self):
        return {"type": "text", "field": "literal"}

    def process_data(self, data):
        x = data.get("literal")
        if not x:
            return None
        return f'"{x}"'


class IRIField(TextField):
    def __init__(self, rdf_name, **kwargs):
        super().__init__(rdf_name, **kwargs)

    @property
    def template(self):
        return {"type": "text", "field": "iri"}

    def process_data(self, data):
        x = data.get("iri")
        if not x:
            return None
        elif not handler.url_regex.match(x):
            raise APIError("Invalid IRI")
        else:
            return f"<{x}>"


class TextAreaField(TextField):
    @property
    def template(self):
        return {"type": "textarea"}


class YearField(Field):
    def __init__(self, rdf_name, **kwargs):
        super().__init__(rdf_name, **kwargs)

    @property
    def template(self):
        return {"type": "text"}

    def process_data(self, data):
        x = data.get("literal")
        if not x:
            return None
        try:
            return int(x)
        except ValueError:
            raise APIError("Invalid year")


class PredefinedInstanceField(IRIField):
    def __init__(self, rdf_name, cls_iri, subclass=False, **kwargs):
        super().__init__(rdf_name, **kwargs)
        self.is_literal = False
        self.filter = [f"{'rdfs:subClassOf' if subclass else 'a'} <{cls_iri}>"]
        self.cls_iri = cls_iri
        self.subclass = subclass
        self.handler = handler.IRIHandler()

    @property
    def template(self):
        return {"type": "select", "class": self.cls_iri, "subclass": self.subclass}


class FactoryField(IRIField):
    def __init__(self, factory, **kwargs):
        super(FactoryField, self).__init__(**kwargs)
        self.factory = factory
        self._widget = DynamicFactoryArrayWidget(
            subwidget_form=widget._factory_field(factory)
        )
        self.is_literal = False
        self.handler = handler.IRIHandler()

    @property
    def spec(self):
        return dict(factory=self.factory._factory_id, **super(FactoryField, self).spec)

    @property
    def template(self):
        return None

    @property
    def _label_option(self):
        custom = self.factory._label_option("?o", "?lo")
        if custom:
            return custom
        return super(FactoryField, self)._label_option


class Container(handler.Rederable):
    def __init__(self, field):
        self.field = field
        self.values = []

    def to_json(self):
        for v in self.values:
            if isinstance(v, rl.Literal):
                yield v
            elif isinstance(v, (rl.URIRef, rl.BNode)):
                yield dict(iri=v)
            elif isinstance(v, factory.RDFFactory):
                d = dict(iri=v.iri.values[0])
                if v.label:
                    d["label"] = v.label
                yield d
            elif isinstance(v, handler.NamedIRI):
                yield dict(iri=v.iri, label=v.label)
            else:
                raise Exception(v)
