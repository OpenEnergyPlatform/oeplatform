from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Namespace
from itertools import chain
from oeplatform.settings import RDF_DATABASES
from django.utils.html import conditional_escape, format_html, format_html_join, mark_safe

OEO = Namespace("http://openenergy-platform.org/ontology/oeo/")
OEO_KG = Namespace("http://openenergy-platform.org/thing/")
SIO = Namespace("http://semanticscience.org/resource/")
dbo = Namespace("http://dbpedia.org/ontology/")
dc = Namespace("http://purl.org/dc/elements/1.1/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
npg = Namespace("http://ns.nature.com/terms/")
obo = Namespace("http://purl.obolibrary.org/obo/")
schema = Namespace("https://schema.org/")
xsd = Namespace("http://www.w3.org/2001/XMLSchema#")
rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")


class Object:
    def __init__(self):
        pass


class Handler:
    def __call__(self, value, **kwargs):
        raise NotImplementedError


class Rederable:
    def render(self, **kwargs):
        raise NotImplementedError

    def render_form_field(self, **kwargs):
        raise NotImplementedError


class NamedIRI(Rederable):
    def __init__(self, iri, label):
        self.iri = iri
        self.label = label

    def render(self, **kwargs):
        return format_html("<a href=\"{iri}\">{label}</a>", iri=self.iri, label=self.label)

class DefaultHandler(Handler):
    def __call__(self, value, **kwargs):
        if isinstance(value, dict):
            if "type" in value and "value" in value:
                t = value["type"]
                if t == "uri":
                    if "label" in value:
                        return NamedIRI(value["value"], value["label"]["value"])
                    else:
                        return value["value"]
                else:
                    return value
        elif isinstance(value, list):
            return [self(v) for v in value]



class Field(Rederable):
    _handler = DefaultHandler

    def __init__(self, rdf_name, verbose_name=None, handler: Handler = None):
        self.rdf_name = rdf_name
        self.verbose_name = verbose_name
        self.handler = handler if handler else self._handler()
        self.values = None

    def to_triples(self, subject):
        if self.values is not None:
            for v in self.values:
                yield f"{subject} {self.rdf_name} {v} ."

    def render(self, mode="display", **kwargs):
        it = (self.values if self.values else ["-"])

        if mode == "display":
            f = self._render_atomic_field
        else:
            f = self._render_atomic_form_field

        vals = [(f(v),) for v in it]
        s = format_html(mark_safe("<tr><th><a href=\"{rdfname}\">{vname}</a></th><td>{vals}</td></tr>"), rdfname=self.rdf_name,
                    vname=self.verbose_name, vals=format_html_join(", ", "{}", vals))
        return s

    def _render_atomic_field(self, obj, **kwargs):
        if isinstance(obj, Rederable):
            return obj.render()
        elif isinstance(obj, list):
            return [self._render_atomic_field(o, **kwargs) for o in obj]
        elif isinstance(obj, str):
            return obj
        else:
            raise ValueError(obj)

    def _render_atomic_form_field(self, obj, **kwargs):
        if isinstance(obj, Rederable):
            return obj.render()
        elif isinstance(obj, list):
            return [self._render_atomic_form_field(o, **kwargs) for o in obj]
        elif isinstance(obj, str):
            return obj
        else:
            raise ValueError(obj)


class ConnectionContext:
    def __init__(self):
        c = RDF_DATABASES["knowledge"]

        self.connection = SPARQLWrapper(f"http://{c['host']}:{c['port']}/{c['name']}")
        self.connection.setReturnFormat(JSON)

    def execute(self, entities):
        s = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n" \
            "SELECT ?s ?p ?o ?lo ?lp WHERE "
        s += " UNION ".join(f"{{ ?s ?p ?o. OPTIONAL {{ ?p rdfs:label ?lp . }} . OPTIONAL {{ ?o rdfs:label ?lo . }} . FILTER ( ?s = <{e}> )}}" for e in entities)
        self.connection.setQuery(s)
        return self.connection.query().convert()


class RDFFactory:
    _field_handler = {}
    _direct_parent = None
    classes = Field(rdf_name=rdf.type, verbose_name="Classes")
    label = Field(rdf_name=rdfs.label, verbose_name="Label")

    def __init_subclass__(cls, **kwargs):
        cls._field_handler = {k: getattr(cls, k).handler for k in cls._iter_fields()}
        cls._field_map = {str(getattr(cls, k).rdf_name): k for k in cls._iter_fields()}

    def __init__(self, **kwargs):
        self.additional_fields = {}
        default_handler = DefaultHandler()
        _internal_fields = set(self._iter_fields())
        for k0, v in kwargs.items():
            k = self._field_map.get(k0, k0)
            if k in _internal_fields:
                getattr(self, k).values = v
            else:
                self.additional_fields[k] = v

    @classmethod
    def _iter_fields(cls):
        for k in dir(cls):
            if isinstance(getattr(cls, k), Field):
                yield k

    @classmethod
    def _load(cls, identifiers, context, cache=None):
        if cache is None:
            cache = {str(i): dict(iri=i) for i in identifiers if str(i) not in cache}
        r = context.execute(identifiers)
        triples = [(row["s"]["value"], row["p"]["value"], {**row["o"], **row.get("lo", {})}) for row in r["results"]["bindings"]]

    @classmethod
    def _parse(cls, triples, cache=None):
        if cache is None:
            cache = dict()
        for (s, p, (o, lo)) in triples:
            obj = cache.get(s, dict())
            handler = cls._field_handler.get(p, DefaultHandler())
            o = handler.__call__(o)
            try:
                obj[p].append(o)
            except KeyError:
                obj[p] = [o]
            cache[s] = obj
        return cache

    def save(self, context):
        triples = chain(*(getattr(self, k).to_triples(self.iri) for k in self._iter_fields()), (f"{self.iri} {k} {v}" for k, vs in self.additional_fields.items() for v in vs))
        print("\n".join(triples))

    def render_table(self):
        s = format_html_join("\n", "{}", ((getattr(self, f).render(),) for f in self._iter_fields()))
        return s


class FactoryHandler(Handler):
    def __init__(self, factory, filter_class=False):
        self.factory = factory
        self.filter_class = filter_class

    def __call__(self, value, **kwargs):
        return value


class FactoryField(Field):
    def __init__(self, factory: RDFFactory, **kwargs):
        super(FactoryField, self).__init__(rdf_name=factory._direct_parent, **kwargs)


class Study(RDFFactory):
    _direct_parent = OEO.OEO_00020011
    funding_source = Field(rdf_name=OEO.OEO_00000509, verbose_name="Funding source")
    covers_energy_carrier = Field(rdf_name=obo.BFO_0000051, verbose_name="Covers energy carriers")
    model_calculations = Field(rdf_name=schema.affiliation, verbose_name="Model Calculations")

class Scenario(RDFFactory):
    pass


class Publication(RDFFactory):
    title = Field(rdf_name=dc.title, verbose_name="Title")
    subtitle = Field(rdf_name=dbo.subtitle, verbose_name="Subtitle")
    publication_year = Field(rdf_name=npg.publicationYear, verbose_name="Publication year")
    abstract = Field(rdf_name=dbo.abstract, verbose_name="Abstract")
    url = Field(rdf_name=schema.url, verbose_name="URL")
    authors = Field(rdf_name=OEO.OEO_00000506, verbose_name="Authors")
    about = Field(rdf_name=obo.IAO_0000136, verbose_name="About")


class Institution(RDFFactory):
    _direct_parent = OEO.OEO_00000238
    name = Field(rdf_name=foaf.name, verbose_name="Name")


class Person(RDFFactory):
    _direct_parent = OEO.OEO_00000323
    first_name = Field(rdf_name=foaf.givenName, verbose_name="First name")
    last_name = Field(rdf_name=foaf.familyName, verbose_name="Last name")
    affiliation = Field(rdf_name=schema.affiliation, verbose_name="Affiliation")


class Model(RDFFactory):
    _direct_parent = OEO.OEO_00020011
    url = Field(rdf_name=schema.url, verbose_name="URL")
    name = Field(rdf_name=dc.title, verbose_name="Name")


class ModelCalculation(RDFFactory):
    has_input = Field(rdf_name=obo.RO_0002233, verbose_name="Inputs")
    has_output = Field(rdf_name=obo.RO_0002234, verbose_name="Outputs")
    uses = Field(rdf_name=OEO.OEO_00000501, verbose_name="Involved Models", handler=FactoryHandler(Model))
