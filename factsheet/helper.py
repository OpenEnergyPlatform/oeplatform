"""
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from urllib.parse import urlparse

from rdflib import Graph, URIRef

from factsheet.models import ScenarioBundleAccessControl
from factsheet.oekg.connection import oekg, oeo, oeo_owl
from factsheet.oekg.namespaces import OBO, OEO, RDFS, SKOS, bind_all_namespaces

DATABUS_PREFIX = "https://databus.openenergyplatform.org/"

INTERNAL_TABLE_RE = re.compile(r"(^|/)database/tables/(?P<table>[^/#?]+)($|/)")
LEGACY_DATAEDIT_RE = re.compile(
    r"(^|/)dataedit/view/(?P<schema>[^/]+)/(?P<table>[^/#?]+)($|/)"
)

# TODO: Refactor code to usage of constants below
# Collection of constants to easy DX:
# used to ease code readability, not used cosistently yet
# OEO classes for parts
OEO_SCENARIO = OEO.OEO_00000365  # scenario factsheet
OEO_PUBLICATION = OEO.OEO_00020012  # study report
OEO_MODEL = OEO.OEO_00000277  # model factsheet
OEO_FRAMEWORK = OEO.OEO_00000172  # framework factsheet

# Common props (you already use these elsewhere)
HAS_PART = OBO.BFO_0000051
PUB_UID = OEO.OEO_00390095
PUB_DATE = OEO.OEO_00390096
PUB_DOI = OEO.OEO_00390098
PUB_LINK = OEO.OEO_00390078
PUB_AUTHOR = OEO.OEO_00000506

SCENARIO_YEAR = OEO.OEO_00020440
SCENARIO_REGION = OEO.OEO_00020220
SCENARIO_INTERREG = OEO.OEO_00020222
SCENARIO_DESCRIPTOR = OEO.OEO_00390073

SECTOR_DIVISION = OEO.OEO_00390079
SECTOR = OEO.OEO_00020439
TECHNOLOGY = OEO.OEO_00020438
INSTITUTION_PROP = OEO.OEO_00000510
FUNDING_PROP = OEO.OEO_00000509

HAS_URL_OR_IRI = (
    OEO.OEO_00390094
)  # landing URL on model/framework/scenario/publication nodes (present in your TTL)


PROP_DEFINED_BY = URIRef(
    "https://openenergyplatform.org/ontology/oeo/OEO_00000504"
)  # "is defined by"
PROP_DEFINITION = URIRef("http://purl.obolibrary.org/obo/IAO_0000115")
SECTOR_DEVISIONS = [OEO.OEO_00010056, OEO.OEO_00000242, OEO.OEO_00010304]
PROP_DEFINITION = URIRef("http://purl.obolibrary.org/obo/IAO_0000115")


oekg = bind_all_namespaces(graph=oekg)


def clean_name(name):
    return (
        name.rstrip()
        .lstrip()
        .replace("-", "_")
        .replace(" ", "_")
        .replace("%", "")
        .replace("Ö", "Oe")
        .replace("ö", "oe")
        .replace("/", "_")
        .replace(":", "_")
        .replace("(", "_")
        .replace(")", "_")
        .replace("ü", "ue")
    )


def set_ownership(bundle_uid, user):
    model = ScenarioBundleAccessControl()
    model.owner_user = user
    model.bundle_id = bundle_uid
    model.save()
    return f"The ownership of bundle {bundle_uid} is now set to User {user.name}"


def is_owner(user, bundle_id):
    return ScenarioBundleAccessControl.user_has_access(user, bundle_id)


def search_scenario_type_iris_by_label(label, input):
    for child in input:
        result = None

        if str(child["label"]) == label:
            result = str(child["iri"])
            return result

        elif child.get("children"):
            result = search_scenario_type_iris_by_label(label, child["children"])
            if result:
                return result
    return result


def get_scenario_type_iri(scenario_type_label: str):
    scenario_class = oeo_owl.search_one(
        iri="https://openenergyplatform.org/ontology/oeo/OEO_00000364"
    )
    scenario_subclasses = get_all_sub_classes(scenario_class)

    result = search_scenario_type_iris_by_label(
        label=scenario_type_label, input=scenario_subclasses["children"]
    )

    return result


def get_all_sub_classes(cls, visited=None):
    if visited is None:
        visited = set()

    visited.add(cls.label.first())
    # "value": cls.label.first(),  "label": cls.label.first(), , "iri": cls.iri

    childCount = len(list(cls.subclasses()))
    subclasses = cls.subclasses()

    dict = {
        "name": cls.label.first(),
        "label": cls.label.first(),
        "value": cls.label.first(),
        "iri": cls.iri,
        "definition": oeo.value(OEO[str(cls).split(".")[1]], OBO.IAO_0000115),
    }

    if childCount > 0:
        dict["children"] = [
            get_all_sub_classes(subclass, visited)
            for subclass in subclasses
            if subclass.label.first() not in visited
        ]
    return dict


def _label(g: Graph, node: URIRef):
    lab = g.value(node, RDFS.label)
    return str(lab) if lab else None


def _definition(g: Graph, node: URIRef):
    # Prefer IAO:definition; fall back to SKOS definition or rdfs:comment
    for p in (PROP_DEFINITION, SKOS.definition, RDFS.comment):
        val = g.value(node, p)
        if val:
            return str(val)
    return None


def build_sector_dropdowns_from_oeo(g: Graph):
    sector_divisions_list = []
    sectors_list = []

    for sd in SECTOR_DEVISIONS:
        sd_label = _label(g, sd) or sd.n3(g.namespace_manager)
        sd_def = _definition(g, sd)

        # division dropdown option (+ definition)
        sector_divisions_list.append(
            {
                "class": sd,  # TODO; URIRef; cast to str?
                "label": sd_label,
                "name": sd_label,
                "value": sd_label,
                "sector_division_definition": sd_def,
            }
        )

        # sector individuals: ?sector oeo:is_defined_by ?sd
        for sector in g.subjects(PROP_DEFINED_BY, sd):
            sec_label = _label(g, sector)  # type: ignore
            definition = g.value(sector, PROP_DEFINITION)

            sectors_list.append(
                {
                    "iri": sector,
                    "label": sec_label,
                    "value": sec_label,
                    "sector_division": sd,
                    "sector_difinition": (str(definition) if definition else None),
                }
            )

    return sector_divisions_list, sectors_list


# Study descriptors are OEO terms carrying the annotation property
# "oekg annotation" (OEO_00020425) with the exact value "study descriptor".
# See the OEKG scenario-bundles wayfinder (WF-03 / WF-04): the match is strict —
# terms tagged with the inconsistent value "study descriptor tag" are NOT
# included; that is an ontology data issue to fix upstream in the OEO.
OEKG_ANNOTATION = OEO.OEO_00020425
STUDY_DESCRIPTOR_VALUE = "study descriptor"

_study_descriptors_cache = None


def build_study_descriptors_from_oeo(g: Graph):
    """Return study descriptors as ``[label, iri, definition]`` triples.

    Strict: only terms annotated with ``OEO_00020425`` ("oekg annotation") whose
    value is exactly ``"study descriptor"``. Labels come from ``rdfs:label`` and
    definitions from the ontology (IAO / SKOS / rdfs:comment). Matches the shape
    of the former hardcoded ``StudyKeywords`` array in the React frontend.

    Memoized on first call — the OEO only changes when the process restarts.
    """
    global _study_descriptors_cache
    if _study_descriptors_cache is not None:
        return _study_descriptors_cache

    descriptors = []
    for term, value in g.subject_objects(OEKG_ANNOTATION):
        if str(value).strip() != STUDY_DESCRIPTOR_VALUE:
            continue
        label = _label(g, term) or term.n3(g.namespace_manager)
        definition = _definition(g, term)
        descriptors.append([label, str(term), definition or ""])

    descriptors.sort(key=lambda d: d[0].lower())
    _study_descriptors_cache = descriptors
    return descriptors


def parse_dataset_iri(iri: str | None) -> dict:
    """
    Parse internal and external dataset URLs which have ben added to the OEKG to
    determine a tables ID.

    :param iri: IRI of the dataset, can be an external databus URL or
                an internal OEP URL
    :type iri: str | None
    :return: Description
    :rtype: dict[Any, Any]
    """

    if not iri:
        return {"kind": "unknown", "url": None}

    u = str(iri).strip()

    # External: Databus
    if u.startswith(DATABUS_PREFIX):
        path = urlparse(u).path.strip("/")  # zl_energie/ZLE/...
        return {"kind": "databus", "url": u, "external_id": path}

    # Normalize relative URLs into a parseable absolute URL
    parsed = urlparse(u if "://" in u else f"http://dummy/{u.lstrip('/')}")
    path = parsed.path.lstrip("/")

    # New internal
    m = INTERNAL_TABLE_RE.search(path)
    if m:
        return {"kind": "oep_table", "url": u, "table_name": m.group("table")}

    # Legacy internal
    m = LEGACY_DATAEDIT_RE.search(path)
    if m:
        return {
            "kind": "oep_table",
            "url": u,
            "schema": m.group("schema"),
            "table_name": m.group("table"),
        }

    return {"kind": "unknown", "url": u}
