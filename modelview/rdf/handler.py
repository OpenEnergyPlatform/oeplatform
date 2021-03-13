from django.utils.html import format_html
from rdflib import Graph, URIRef, Literal


class Rederable:
    def render(self, **kwargs):
        raise NotImplementedError

    def render_form_field(self, **kwargs):
        raise NotImplementedError


class Handler:
    def __call__(self, value, context, graph, **kwargs):
        raise NotImplementedError

    def from_structure(self, value, **kwargs):
        raise NotImplementedError


class NamedIRI(Rederable):
    def __init__(self, iri, label):
        self.iri = iri
        self.label = label

    def render(self, **kwargs):
        return format_html(
            '<a href="{iri}">{label}</a>', iri=self.iri, label=self.label
        )


class DefaultHandler(Handler):
    def __call__(self, value, context, graph: Graph, **kwargs):
        if isinstance(value, URIRef):
            label = graph.label(value, None)
            if label is not None:
                return NamedIRI(value, label)
            else:
                return value
        elif isinstance(value, list):
            return [self.__call__(v, context, graph) for v in value if v]
        elif isinstance(value, str):
            return value
        else:
            raise Exception(value)

    def from_structure(self, value, **kwargs):
        if isinstance(value, URIRef):
            return value
        elif isinstance(value, list):
            return [self.from_structure(v, **kwargs) for v in value if v]
        elif isinstance(value, str):
            return Literal(value)
        else:
            raise Exception(value)


class LabelHandler(DefaultHandler):
    def __call__(self, value, context, graph: Graph, **kwargs):
        pass


class IRIHandler(DefaultHandler):
    def __call__(self, value, context, graph: Graph, **kwargs):
        return value

    def from_structure(self, value, **kwargs):
        return [URIRef(v) for v in value if v]


class FactoryHandler(Handler):
    def __init__(self, factory, filter_class=False):
        self.factory = factory
        self.filter_class = filter_class

    def __call__(self, value, context, graph, **kwargs):
        d = self.factory._load_many(value, context, graph)
        return [d[v] for v in value if v]

    def from_structure(self, value, **kwargs):
        if isinstance(value, list):
            return [self.from_structure(v, **kwargs) for v in value]
        else:
            return self.factory._parse_from_structure(value, **kwargs)
