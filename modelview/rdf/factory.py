from abc import ABC

from rdflib import BNode, Literal, URIRef

import modelview.rdf.namespace as ns
from modelview.rdf import connection, field

FACTORIES = {}


def get_factory_templates():
    return {n: f.build_structure_spec() for n, f in FACTORIES.items()}


def get_factory(identifier):
    return FACTORIES[identifier]


class RDFFactory(ABC):
    _field_handler = {}
    _factory_id = None
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
        if cls._factory_id is not None:
            FACTORIES[cls._factory_id] = cls
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
        _internal_fields = set(self.iter_field_names())
        for f in _internal_fields:
            getattr(self, f).field_name = f
        for k, v in kwargs.items():
            if k in _internal_fields:
                getattr(self, k).values = v
            else:
                self.additional_fields[k] = v

    @classmethod
    def from_iri(cls, iri):
        return cls

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
        cached_objects = {i: cache[i] for i in identifiers if i in cache}
        new_items = [i for i in identifiers if i not in cache]
        result = context.query_all_objects(new_items, cls._fields.items())
        # head = result["head"]
        d = dict()
        # model_inputs = []
        for t in result["results"]["bindings"]:
            if "s" in t:
                s = cls._read_value(t["s"])
                o = cls._read_value(t.get("o"))
                # lo = cls._read_value(t.get("lo"))
                # lp = cls._read_value(t.get("lp"))
                fname = t["fname"]["value"]
                d[s] = d.get(s, dict())
                res = ""
                if fname == "has_input" or fname == "has_output":
                    res = context.query_one_object(o, "<https://ns.schema.org/url>")[
                        "results"
                    ]["bindings"][0]["object"]["value"]
                d[s][fname] = d[s].get(fname, []) + [(o, res)]

        cached_objects.update(
            {
                i: cls._parse(i, context, d[i], cache=cache) if i in d else cls(iri=i)
                for i in identifiers
            }
        )
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
        return cls._load_many(
            [identifier],
            context,
        )[identifier]

    @classmethod
    def _find_field(cls, predicate_iri, obj):
        # TODO: There should be a fallback here for additional fields
        return cls._field_map.get(predicate_iri, None)

    @classmethod
    def _parse(cls, identifier, context, obj, cache=None):
        if cache is None:
            cache = dict()
        # obj = cache.get(identifier, dict())
        skipped = set()
        if skipped:
            print("Warning! Some predicates were not processed:", skipped)
        res = cache[identifier] = cls(
            iri=identifier,
            **{p: cls._fields[p].handler(os, context) for p, os in obj.items()},
        )
        print(res)
        return res

    @classmethod
    def _parse_from_structure(cls, structure: dict, identifier=None, cache=None):

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

    def to_json(self):
        return {f: list(getattr(self, f).to_json()) for f in self.iter_field_names()}

    @classmethod
    def build_structure_spec(cls):
        return {f: fld.spec for f, fld in cls._fields.items()}

    @classmethod
    def _label_option(cls, o, lo):
        return None

    @classmethod
    def load_all_instances(cls, context):
        result = context.query_all_factory_instances(cls)
        insts = []
        for t in result["results"]["bindings"]:
            if "s" in t:
                s = cls._read_value(t["s"])
                label = cls._read_value(t.get("ls"))
                insts.append(dict(element=s.split("/")[-1], label=label or s))
        return insts


class IRIFactory(RDFFactory):
    _fields = dict(
        iri=field.IRIField(rdf_name=ns.dbo.abbreviation, verbose_name="Abbreviation")
    )


class Institution(RDFFactory):
    _factory_id = "institution"
    _direct_parent = ns.OEO.OEO_00000238
    _label_field = "name"
    _fields = dict(
        name=field.TextField(rdf_name=ns.foaf.name, verbose_name="Name"),
        address=field.TextField(rdf_name=ns.foaf.address, verbose_name="Address"),
    )

    @classmethod
    def _label_option(cls, o, lo):
        return f"{o} <{cls._fields['name'].rdf_name}> {lo}."


class Person(RDFFactory):
    _direct_parent = ns.OEO.OEO_00000323
    _factory_id = "person"
    _fields = dict(
        first_name=field.TextField(
            rdf_name=ns.foaf.givenName, verbose_name="First name"
        ),
        last_name=field.TextField(
            rdf_name=ns.foaf.familyName, verbose_name="Last name"
        ),
        affiliation=field.FactoryField(
            factory=Institution,
            rdf_name=ns.schema.affiliation,
            verbose_name="Affiliation",
        ),
    )

    @classmethod
    def _label_option(cls, o, lo):
        return f"{o} <{cls._fields['last_name'].rdf_name}> {lo}."


class AnalysisScope(RDFFactory):
    _factory_id = "scope"
    _direct_parent = ns.OEO_KG.AnalysisScope
    _fields = dict(
        is_defined_by=field.IRIField(
            rdf_name=ns.OEO.OEO_00000504, verbose_name="is defined by"
        ),
        covers_sector=field.PredefinedInstanceField(
            rdf_name=ns.OEO.OEO_00000505,
            verbose_name="Sectors",
            cls_iri=ns.OEO.OEO_00000367,
        ),
        covers_energy_carrier=field.PredefinedInstanceField(
            rdf_name=ns.OEO.OEO_00000523,
            cls_iri=ns.OEO.OEO_00000331,
            verbose_name="Covers energy carriers",
            subclass=True,
        ),
        covers_energy=field.PredefinedInstanceField(
            rdf_name=ns.OEO.OEO_00000523,
            cls_iri=ns.OEO.OEO_00000150,
            verbose_name="Related to energy",
            subclass=True,
        ),
    )


class Scenario(RDFFactory):
    _direct_parent = ns.OEO.OEO_00000364
    _label_field = "name"
    _factory_id = "scenario"
    _fields = dict(
        abbreviation=field.TextField(
            rdf_name=ns.dbo.abbreviation, verbose_name="Abbreviation"
        ),
        abstract=field.TextField(
            rdf_name=ns.dbo.abstract,
            verbose_name="Abstract",
            help_text="A short description of this scenario",
        ),
        name=field.TextField(
            rdf_name=ns.foaf.name,
            verbose_name="Name",
            help_text="Name of this scenario",
        ),
        analysis_scope=field.FactoryField(
            AnalysisScope,
            rdf_name=ns.OEO.OEO_00000504,
            inverse=True,
            verbose_name="Analysis Scope",
        ),
    )

    @classmethod
    def _label_option(cls, o, lo):
        return f"{o} <{cls._fields['name'].rdf_name}> {lo}"


class Publication(RDFFactory):
    _factory_id = "publication"
    _direct_parent = ns.OEO.OEO_00020012
    _fields = dict(
        title=field.TextField(
            rdf_name=ns.dc.title,
            verbose_name="Title",
            help_text="Title of the publication",
        ),
        subtitle=field.TextField(rdf_name=ns.dbo.subtitle, verbose_name="Subtitle"),
        publication_year=field.TextField(
            rdf_name=ns.npg.publicationYear,
            verbose_name="Publication year",
            help_text="Year this publication was published in",
        ),
        abstract=field.TextField(
            rdf_name=ns.dbo.abstract,
            verbose_name="Abstract",
            help_text="Abstract of the publication",
        ),
        url=field.TextField(
            rdf_name=ns.schema.url,
            verbose_name="URL",
            help_text="Link to this publication",
        ),
        authors=field.FactoryField(
            rdf_name=ns.OEO.OEO_00000506,
            verbose_name="Authors",
            help_text="Authors of this publication",
            factory=Person,
        ),
        about=field.TextField(
            rdf_name=ns.obo.IAO_0000136,
            verbose_name="About",
            help_text="Elements of this publication",
        ),
    )

    @classmethod
    def _label_option(cls, o, lo):
        return f"{o} <{cls._fields['title'].rdf_name}> {lo}."


class Model(RDFFactory):
    _factory_id = "model"
    _direct_parent = ns.OEO.OEO_00020011
    _fields = dict(
        url=field.IRIField(rdf_name=ns.schema.url, verbose_name="URL"),
        name=field.TextField(rdf_name=ns.dc.title, verbose_name="Name"),
    )

    @classmethod
    def _label_option(cls, o, lo):
        return f"{o} <{cls._fields['name'].rdf_name}> {lo}"


class Dataset(RDFFactory):
    _factory_id = "dataset"
    _fields = dict(
        url=field.TextField(rdf_name=ns.schema.url, verbose_name="URL"),
    )

    @property
    def label(self):
        return self.url.values[0]


class ModelCalculation(RDFFactory):
    _factory_id = "model_calculation"
    _fields = dict(
        has_input=field.FactoryField(
            rdf_name=ns.obo.RO_0002233, factory=Dataset, verbose_name="Inputs"
        ),
        has_output=field.FactoryField(
            rdf_name=ns.obo.RO_0002234, factory=Dataset, verbose_name="Outputs"
        ),
        uses=field.IRIField(
            rdf_name=ns.OEO.OEO_00000501,
            verbose_name="Involved Models",
        ),
    )
    model_inputs = field.FactoryField(
        rdf_name=ns.obo.RO_0002233, factory=Dataset, verbose_name="Inputs"
    )


class Study(RDFFactory):
    _factory_id = "study"
    _direct_parent = ns.OEO.OEO_00020011
    _fields = dict(
        funding_source=field.FactoryField(
            Institution,
            rdf_name=ns.OEO.OEO_00000509,
            verbose_name="Funding source",
        ),
        covers_energy_carrier=field.PredefinedInstanceField(
            rdf_name=ns.OEO.OEO_00000523,
            cls_iri=ns.OEO.OEO_00000331,
            verbose_name="Covers energy carriers",
            subclass=True,
        ),
        covers_energy=field.PredefinedInstanceField(
            rdf_name=ns.OEO.OEO_00000523,
            cls_iri=ns.OEO.OEO_00000150,
            verbose_name="Related to energy",
            subclass=True,
        ),
        model_calculations=field.FactoryField(
            rdf_name=ns.obo.BFO_0000051,
            factory=ModelCalculation,
            filter=[f"a <{ns.OEO.OEO_00000275}>"],
            verbose_name="Model Calculations",
        ),
        published_in=field.FactoryField(
            Publication,
            rdf_name=ns.obo.IAO_0000136,
            inverse=True,
            verbose_name="Publications",
        ),
        scenarios=field.FactoryField(
            Scenario,
            rdf_name=ns.obo.RO_0000057,
            verbose_name="Scenarios",
        ),
    )

    @classmethod
    def _label_option(cls, o, lo):
        return f"_:b <{cls._fields['published_in'].rdf_name}> {o}; <{ns.dc.title}> {lo}"
