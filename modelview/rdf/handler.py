import re

from rdflib import Literal, URIRef

url_regex = re.compile(
    r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$"  # noqa
)


def is_iri(value):
    return url_regex.match(value)


class Rederable:
    def render(self, **kwargs):
        raise NotImplementedError


class Handler:
    def __call__(self, value, context, **kwargs):
        raise NotImplementedError

    def from_structure(self, value, **kwargs):
        raise NotImplementedError


class NamedIRI:
    def __init__(self, iri, label):
        self.iri = iri
        self.label = label

    def __str__(self):
        return str(self.iri)


class NamedElement:
    def __init__(self, element, label):
        self.element = element
        self.label = label

    def __str__(self):
        return self.label


class DefaultHandler(Handler):
    def __call__(self, value, context, **kwargs):
        if isinstance(value, tuple):
            value, label = value
            value = self.__call__(value, context)
            if label:
                return NamedIRI(value, label)
            else:
                return value
        if isinstance(value, URIRef):
            return value
        elif isinstance(value, list):
            return [self.__call__(v, context) for v in value if v]
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
    def __call__(self, value, context, **kwargs):
        pass


class IRIHandler(DefaultHandler):
    def __call__(self, value, context, **kwargs):
        if isinstance(value, list):
            return [self.__call__(v, context) for v in value]
        else:
            value, label = value
            if label:
                return NamedIRI(value, label)
            else:
                return value

    def from_structure(self, value, **kwargs):
        return [URIRef(v) for v in value if v]
