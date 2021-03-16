from abc import ABC
from django.utils.html import format_html, format_html_join, mark_safe
from itertools import chain
from rdflib import Graph, BNode, URIRef, Literal
import json
from modelview.rdf import handler, field, connection
from modelview.rdf.namespace import *


class RDFFactory(handler.Rederable, ABC):
    _field_handler = {}
    _direct_parent = None
    _fields = {}
    _label_field = None

    @classmethod
    def doc(self):
        s = f"""Factory class for {self._direct_parent}. This class has the following fields: 

"""
        for f in self.iter_field_names():
            fld = getattr(self, f)
            s += f"* `{f} <{field.rdf_name}>`_ ({fld.rdf_name})"
            if fld.help_text is not None:
                s += ": " + fld.help_text
            s += "\n"
        s += "\n"
        return s

    def __init_subclass__(cls, **kwargs):
        #cls.fallback_field = "additional_fields"
        #cls._fields[cls.fallback_field] = field.Field(rdf_name=rdf.type, verbose_name="additional")
        cls._fields["classes"] = field.IRIField(rdf_name=rdf.type, verbose_name="Classes", hidden=True)
        cls._field_map = {f.rdf_name: k for k, f in cls._fields.items()}
        cls._fields["iri"] = field.IRIField(None, hidden=True)
        cls._field_handler = {f: f.handler for k, f in cls._fields.items()}
        if cls._label_field is None:
            cls._label_field = "iri"


    def __init__(self, iri=None, **kwargs):
        for fld_name, fld in self._fields.items():
            setattr(self, fld_name, field.Container(fld))
        if iri:
            if isinstance(iri, list):
                assert len(iri) <= 1, "Too many IRIs"
                iri = iri[0]
        self.iri.values = [iri] if iri else []
        self.classes.values = kwargs.get("classes", [])
        default_handler = handler.DefaultHandler()
        _internal_fields = set(self.iter_field_names())
        for f in _internal_fields:
            getattr(self, f).field_name = f
        for k, v in kwargs.items():
            if k in _internal_fields:
                getattr(self, k).values = v
            else:
                self.additional_fields[k] = v

    def iter_fields(self):
        """Returns an iterator of all fields in this factory"""
        return (getattr(self, k) for k in self.iter_field_names())

    def iter_field_names(self):
        """Returns an iterator of all field names in this factory"""
        return self._fields.keys()

    @classmethod
    def _load_many(cls, identifiers, context, cache=None):
        if cache is None:
            cache = dict()
        cached_objects = {i:cache[i] for i in identifiers if i in cache}
        new_items = [i for i in identifiers if i not in cache]
        result = context.query_all_objects(new_items, cls._fields.items())
        head = result["head"]
        d = dict()
        for t in result["results"]["bindings"]:
            if "s" in t:
                s = cls._read_value(t["s"])
                o = cls._read_value(t.get("o"))
                lo = cls._read_value(t.get("lo"))
                lp = cls._read_value(t.get("lp"))
                fname = t["fname"]["value"]
                d[s] = d.get(s, dict())
                d[s][fname] = d[s].get(fname, []) + [(o, lo)]
        cached_objects.update({i: cls._parse(i, context, d[i], cache=cache) for i in identifiers})
        return cached_objects

    @staticmethod
    def _read_value(v):
        if isinstance(v, dict):
            t = v["type"]
            if t == "uri":
                return URIRef(v["value"])
            if t == "literal":
                return Literal(v["value"])
            if t == "bnode":
                return BNode(v["value"])
        if v is None:
            return None
        raise Exception(v)



    @classmethod
    def _load_one(cls, identifier, context: connection.ConnectionContext):
        return cls._load_many([identifier], context,)[identifier]

    @classmethod
    def _find_field(cls, predicate_iri, obj):
        #TODO: There should be a fallback here for additional fields
        return cls._field_map.get(predicate_iri, None)

    @classmethod
    def _parse(cls, identifier, context, obj, cache=None):
        if cache is None:
            cache = dict()
        #obj = cache.get(identifier, dict())
        skipped = set()
        if skipped:
            print("Warning! Some predicates were not processed:", skipped)
        res = cache[identifier] = cls(iri=identifier,
            **{
                p: cls._fields[p].handler(
                    os, context
                )
                for p, os in obj.items()
            }
        )
        return res

    @classmethod
    def _parse_from_structure(cls, structure:dict, identifier=None, cache=None):
        res = cls(
            **{
                p: cls._fields[p].handler.from_structure(
                    structure[p],
                )
                for p in structure
            }
        )

        if identifier:
            res.iri = identifier
            cache[identifier] = res
        return res

    def _insert(self, d):
        s0 = self.__class__(**d)

    def merge(self, second, path):
        head, iri = path.pop()
        first_field = getattr(self, head)
        second_field = getattr(second, head)
        first_field.merge(second_field, iri, path)

    def to_triples(self, iri=None):
        iri = iri or self.iri.values[0]
        return list(chain(
            *(k.to_triples(iri) for k in self.iter_fields())
        ))

    def to_graph(self):
        g = Graph()
        for t in self.to_triples():
            g.add(t)
        return g

    def save(self, context):

        print("\n".join(self.to_triples()))

    def render(self, **kwargs):
        return format_html(
            mark_safe('<table class="table">{}</table>'), self.render_table()
        )

    def render_table(self):
        s = format_html_join("\n", "{}", ((f.render(),) for f in self.iter_fields() if not f.field.hidden))
        return s

    @classmethod
    def structure_spec(cls):
        return json.dumps(cls.build_structure_spec())

    @classmethod
    def build_structure_spec(cls):
        l = []
        for f, field in cls._fields.items():
            d = dict(
                id=f,
                verbose_name=field.verbose_name,
                help_text=field.help_text,
            )
            t = field._widget.get_structure()
            if isinstance(t, str):
                d["template"] = t
            else:
                d["substructure"] = t
            l.append(d)
        return l

    @classmethod
    def build_template_structure(cls, prefix=""):
        d = dict()
        for f, field in cls._fields.items():
            new_prefix = prefix + "." + f if prefix else f
            d.update(**field._widget.build_template_structure(new_prefix))
        return d

    @property
    def label(self):
        try:
            return getattr(self, self._label_field).values[0]
        except:
            return None

    @classmethod
    def load_all_instances(cls, context: connection.ConnectionContext):
        results = context.load_all(filter=[f"a <{cls._direct_parent}>"])
        return [handler.NamedElement(row['iri']['value'].split("/")[-1], handler.NamedIRI(row.get('l', dict()).get("value"), row['iri']['value']) if row.get('l', dict()).get("value")  else row['iri']['value']) for row in results["results"]["bindings"]]


class IRIFactory(RDFFactory):
    _fields = dict(
    iri = field.Field(rdf_name=dbo.abbreviation, verbose_name="Abbreviation"))


class Institution(RDFFactory, handler.Rederable):
    _direct_parent = OEO.OEO_00000238
    _label_field = "name"
    _fields = dict(
    name = field.Field(rdf_name=foaf.name, verbose_name="Name"),
    address = field.Field(rdf_name=foaf.address, verbose_name="Address"))

    @property
    def label(self):
        return self.name.values[0]

    def render(self, **kwargs):
        return self.label


class Person(RDFFactory, handler.Rederable):
    _direct_parent = OEO.OEO_00000323
    _fields = dict(
    first_name = field.Field(rdf_name=foaf.givenName, verbose_name="First name"),
    last_name = field.Field(rdf_name=foaf.familyName, verbose_name="Last name"),
    affiliation = field.FactoryField(factory=Institution, rdf_name=schema.affiliation, verbose_name="Affiliation",handler=handler.FactoryHandler(Institution),))

    @property
    def label(self):
        return self.first_name.values[0] + " " + self.last_name.values[0]

    def render(self, **kwargs):
        return self.label


class AnalysisScope(RDFFactory):
    _fields = dict(
    is_defined_by = field.Field(rdf_name=OEO.OEO_00000504, verbose_name="is defined by"),
    covers_sector = field.Field(rdf_name=OEO.OEO_00000505, verbose_name="Sectors"),
    covers = field.Field(rdf_name=OEO.OEO_00000522, verbose_name="Covers"))


class Scenario(RDFFactory):
    _direct_parent = OEO.OEO_00000364
    _label_field = "name"
    _fields = dict(
    abbreviation = field.Field(rdf_name=dbo.abbreviation, verbose_name="Abbreviation"),
    abstract = field.Field(
        rdf_name=dbo.abstract,
        verbose_name="Abstract",
        help_text="A short description of this scenario",
    ),
    name = field.Field(
        rdf_name=foaf.name,
        verbose_name="Abstract",
        help_text="A short description of this scenario",
    ),
    analysis_scope = field.FactoryField(
        AnalysisScope,
        rdf_name=OEO.OEO_00000504,
        inverse=True,
        verbose_name="Analysis Scope",
        handler=handler.FactoryHandler(AnalysisScope),
    ))


class Publication(RDFFactory):
    _fields = dict(
    title = field.Field(
        rdf_name=dc.title, verbose_name="Title", help_text="Title of the publication"
    ),
    subtitle = field.Field(rdf_name=dbo.subtitle, verbose_name="Subtitle"),
    publication_year = field.Field(
        rdf_name=npg.publicationYear,
        verbose_name="Publication year",
        help_text="Year this publication was published in",
    ),
    abstract = field.Field(
        rdf_name=dbo.abstract,
        verbose_name="Abstract",
        help_text="Abstract of the publication",
    ),
    url = field.Field(
        rdf_name=schema.url, verbose_name="URL", help_text="Link to this publication"
    ),
    authors = field.FactoryField(
        rdf_name=OEO.OEO_00000506,
        verbose_name="Authors",
        help_text="Authors of this publication",
        factory=Person,
        handler=handler.FactoryHandler(Person),
    ),
    about = field.Field(
        rdf_name=obo.IAO_0000136,
        verbose_name="About",
        help_text="Elements of this publication",
    ))

    _label_field = "title"


class Model(RDFFactory):
    _direct_parent = OEO.OEO_00020011
    _fields = dict(
    url = field.Field(rdf_name=schema.url, verbose_name="URL"),
    name = field.Field(rdf_name=dc.title, verbose_name="Name"))


class Dataset(RDFFactory):
    _fields = dict(
        url=field.IRIField(rdf_name=schema.url, verbose_name="URL"),
    )

    @property
    def label(self):
        return self.url.values[0]

    def render(self, **kwargs):
        return format_html("<a href={0}>{0}</a>", self.label)


class ModelCalculation(RDFFactory):
    _fields = dict(
        has_input= field.FactoryField(rdf_name=obo.RO_0002233, factory=Dataset, verbose_name="Inputs"),
        has_output = field.FactoryField(rdf_name=obo.RO_0002234, factory=Dataset, verbose_name="Outputs"),
        uses = field.Field(
            rdf_name=OEO.OEO_00000501,
            verbose_name="Involved Models",
            handler=handler.FactoryHandler(Model),
        ))


class Study(RDFFactory):
    _direct_parent = OEO.OEO_00020011
    _fields = dict(
        funding_source=field.FactoryField(
            Institution,
            rdf_name=OEO.OEO_00000509,
            verbose_name="Funding source",
            handler=handler.FactoryHandler(Institution),
        ),
        covers_energy_carrier=field.PredefinedInstanceField(
            rdf_name=OEO.OEO_00000523, filter=[f"<{rdfs.subClassOf}> <{OEO.OEO_00000331}>"], verbose_name="Covers energy carriers", subclass=True,
        ),
        covers_energy=field.PredefinedInstanceField(
            rdf_name=OEO.OEO_00000523, filter=[f"<{rdfs.subClassOf}> <{OEO.OEO_00000150}>"], verbose_name="Related to energy", subclass=True,
        ),

        model_calculations=field.FactoryField(
            rdf_name=obo.BFO_0000051, factory=ModelCalculation, filter=[f"a <{OEO.OEO_00000275}>"], verbose_name="Model Calculations", handler=handler.FactoryHandler(ModelCalculation),
        ),
        published_in=field.FactoryField(
            Publication,
            rdf_name=obo.IAO_0000136,
            inverse=True,
            verbose_name="Publications",
            handler=handler.FactoryHandler(Publication),
        ),

    )
